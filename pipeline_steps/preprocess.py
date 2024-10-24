import pandas as pd  # Importa pandas para manipulação de dados
import numpy as np  # Importa numpy para operações numéricas
import mlflow  # Importa mlflow para rastreamento de experimentos
from mlflow.data.pandas_dataset import PandasDataset  # Importa PandasDataset do MLflow
from time import gmtime, strftime  # Importa funções de tempo
from sklearn.preprocessing import MinMaxScaler, LabelEncoder  # Importa ferramentas de pré-processamento

def preprocess(
    input_data_s3_path,  # Caminho S3 para os dados de entrada
    output_s3_prefix,  # Prefixo S3 para os dados de saída
    tracking_server_arn,  # ARN do servidor de rastreamento MLflow
    experiment_name=None,  # Nome do experimento (opcional)
    pipeline_run_name=None,  # Nome da execução do pipeline (opcional)
    run_id=None,  # ID da execução (opcional)
):
    
  """
    Pré-processa dados de entrada, divide em conjuntos de treino/validação/teste e salva no S3.

    Esta função realiza as seguintes operações:
    1. Carrega dados do S3
    2. Realiza engenharia de features (criação de novas variáveis, codificação, etc.)
    3. Divide os dados em conjuntos de treino, validação e teste
    4. Salva os conjuntos de dados processados de volta no S3
    5. Registra métricas e parâmetros no MLflow

    Args:
        input_data_s3_path (str): Caminho S3 para o arquivo CSV de entrada.
        output_s3_prefix (str): Prefixo S3 para salvar os arquivos de saída.
        tracking_server_arn (str): ARN do servidor de rastreamento MLflow.
        experiment_name (str, optional): Nome do experimento MLflow. Se None, um nome padrão será usado.
        pipeline_run_name (str, optional): Nome da execução do pipeline MLflow. Se None, nenhuma execução de pipeline será criada.
        run_id (str, optional): ID de uma execução MLflow existente. Se None, uma nova execução será criada.

    Returns:
        dict: Dicionário contendo os caminhos S3 para os dados processados e informações do MLflow:
            - 'train_data': Caminho para os dados de treinamento
            - 'validation_data': Caminho para os dados de validação
            - 'test_x_data': Caminho para os dados de teste (features)
            - 'test_y_data': Caminho para os dados de teste (target)
            - 'baseline_data': Caminho para os dados de linha de base
            - 'experiment_name': Nome do experimento MLflow
            - 'pipeline_run_id': ID da execução do pipeline MLflow (se aplicável)

    Raises:
        Exception: Se ocorrer qualquer erro durante o processamento.

    Note:
        Esta função utiliza o MLflow para rastreamento de experimentos e logging.
        Certifique-se de que o servidor MLflow está configurado corretamente antes de chamar esta função.
    """    
    try:
        suffix = strftime('%d-%H-%M-%S', gmtime())  # Cria um sufixo de tempo único
        mlflow.set_tracking_uri(tracking_server_arn)  # Define o URI de rastreamento do MLflow
        experiment = mlflow.set_experiment(experiment_name=experiment_name if experiment_name else f"{preprocess.__name__ }-{suffix}")  # Define ou cria um experimento
        pipeline_run = mlflow.start_run(run_name=pipeline_run_name) if pipeline_run_name else None  # Inicia uma execução de pipeline se o nome for fornecido
        run = mlflow.start_run(run_id=run_id) if run_id else mlflow.start_run(run_name=f"processing-{suffix}", nested=True)  # Inicia uma execução MLflow

        # Carrega os dados
        df_data = pd.read_csv(input_data_s3_path, sep=";")  # Lê o CSV de entrada

        input_dataset = mlflow.data.from_pandas(df_data, source=input_data_s3_path)  # Cria um dataset MLflow
        mlflow.log_input(input_dataset, context="raw_input")  # Registra o dataset de entrada
        
        target_col = "y"  # Define a coluna alvo
    
        # Cria uma variável indicadora para contatos prévios
        df_data["no_previous_contact"] = np.where(df_data["pdays"] == 999, 1, 0)
    
        # Cria um indicador para indivíduos não empregados ativamente
        df_data["not_working"] = np.where(
            np.in1d(df_data["job"], ["student", "retired", "unemployed"]), 1, 0
        )
    
        # Remove colunas não utilizadas para modelagem
        df_model_data = df_data.drop(
            ["duration", "emp.var.rate", "cons.price.idx", "cons.conf.idx", "euribor3m", "nr.employed"],
            axis=1,
        )
    
        # Define bins e labels para categorização de idade
        bins = [18, 30, 40, 50, 60, 70, 90]
        labels = ['18-29', '30-39', '40-49', '50-59', '60-69', '70-plus']
    
        # Categoriza idade e cria variáveis dummy
        df_model_data['age_range'] = pd.cut(df_model_data.age, bins, labels=labels, include_lowest=True)
        df_model_data = pd.concat([df_model_data, pd.get_dummies(df_model_data['age_range'], prefix='age', dtype=int)], axis=1)
        df_model_data.drop('age', axis=1, inplace=True)
        df_model_data.drop('age_range', axis=1, inplace=True)

        # Escala features numéricas
        scaled_features = ['pdays', 'previous', 'campaign']
        df_model_data[scaled_features] = MinMaxScaler().fit_transform(df_model_data[scaled_features])

        # Converte variáveis categóricas em dummies
        df_model_data = pd.get_dummies(df_model_data, dtype=int)  
    
        # Reorganiza o DataFrame com a coluna alvo no início
        df_model_data = pd.concat(
            [
                df_model_data["y_yes"].rename(target_col),
                df_model_data.drop(["y_no", "y_yes"], axis=1),
            ],
            axis=1,
        )

        # Cria e registra o dataset de modelo no MLflow
        model_dataset = mlflow.data.from_pandas(df_data)
        mlflow.log_input(model_dataset, context="model_dataset")
        
        # Embaralha e divide o dataset
        train_data, validation_data, test_data = np.split(
            df_model_data.sample(frac=1, random_state=1729),
            [int(0.7 * len(df_model_data)), int(0.9 * len(df_model_data))],
        )
    
        print(f"## Divisão de dados > treino:{train_data.shape} | validação:{validation_data.shape} | teste:{test_data.shape}")
    
        # Registra parâmetros no MLflow
        mlflow.log_params(
            {
                "full_dataset": df_model_data.shape,
                "train": train_data.shape,
                "validate": validation_data.shape,
                "test": test_data.shape
            }
        )

        # Define caminhos de saída no S3
        train_data_output_s3_path = f"{output_s3_prefix}/train/train.csv"
        validation_data_output_s3_path = f"{output_s3_prefix}/validation/validation.csv"
        test_x_data_output_s3_path = f"{output_s3_prefix}/test/test_x.csv"
        test_y_data_output_s3_path = f"{output_s3_prefix}/test/test_y.csv"
        baseline_data_output_s3_path = f"{output_s3_prefix}/baseline/baseline.csv"
        
        # Salva os datasets processados no S3
        train_data.to_csv(train_data_output_s3_path, index=False, header=False)
        validation_data.to_csv(validation_data_output_s3_path, index=False, header=False)
        test_data[target_col].to_csv(test_y_data_output_s3_path, index=False, header=False)
        test_data.drop([target_col], axis=1).to_csv(test_x_data_output_s3_path, index=False, header=False)
        
        # Salva o dataset de linha de base para monitoramento do modelo
        df_model_data.drop([target_col], axis=1).to_csv(baseline_data_output_s3_path, index=False, header=False)
           
        print("## Processamento de dados concluído. Saindo.")
        
        # Retorna os caminhos dos dados processados e informações do MLflow
        
        return {
            "train_data":train_data_output_s3_path,
            "validation_data":validation_data_output_s3_path,
            "test_x_data":test_x_data_output_s3_path,
            "test_y_data":test_y_data_output_s3_path,
            "baseline_data":baseline_data_output_s3_path,
            "experiment_name":experiment.name,
            "pipeline_run_id":pipeline_run.info.run_id if pipeline_run else ''
        }

    except Exception as e:
        print(f"Exceção no script de processamento: {e}")
        raise e
    finally:
        mlflow.end_run()



# Este código é usado para pré-processar dados e prepará-los para treinamento e avaliação de modelo. 
# Aqui está o que a função `preprocess` faz:

# 1. Configura o MLflow, definindo o URI de rastreamento e o experimento.
# 2. Carrega os dados de um caminho S3 fornecido e registra o dataset bruto no MLflow.
# 3. Realiza pré-processamento nos dados, incluindo:
#    - Criação de variáveis indicadoras para "sem contato prévio" e "não trabalhando".
#    - Remoção de colunas desnecessárias.
#    - Codificação da faixa etária em variáveis binárias.
#    - Escalamento de recursos numéricos usando `MinMaxScaler`.
#    - Codificação de variáveis categóricas em variáveis indicadoras.
#    - Renomeação da coluna alvo para "y".
# 4. Registra o dataset pré-processado no MLflow.
# 5. Divide aleatoriamente os dados em conjuntos de treinamento, validação e teste.
# 6. Registra as formas dos datasets no MLflow.
# 7. Define os caminhos de saída no Amazon S3 para os datasets de treinamento, validação, teste e linha de base.
# 8. Envia os datasets para o Amazon S3.
# 9. Retorna um dicionário contendo os caminhos dos datasets no S3, o nome do experimento e o ID da execução do pipeline.

# O código usa as bibliotecas `pandas`, `numpy`, `mlflow`, `mlflow.data.pandas_dataset` e `sklearn.preprocessing` para carregar,
# pré-processar e dividir os dados, além de interagir com o MLflow.