import numpy as np
import pandas as pd
import xgboost as xgb
import mlflow
from time import gmtime, strftime
from sklearn.metrics import roc_curve, auc
import matplotlib.pyplot as plt
import tarfile
import pickle as pkl
import boto3

def load_model(model_data_s3_uri):
    """
    Carrega um modelo XGBoost a partir de um arquivo .tar.gz armazenado no S3.

    Args:
        model_data_s3_uri (str): URI S3 do arquivo do modelo.

    Returns:
        xgboost.Booster: Modelo XGBoost carregado.
    """
    # Define o nome do arquivo local para o modelo
    model_file = "./xgboost-model.tar.gz"
    
    # Extrai o nome do bucket e a chave do URI S3
    bucket, key = model_data_s3_uri.replace("s3://", "").split("/", 1)
    
    # Baixa o arquivo do modelo do S3
    boto3.client("s3").download_file(bucket, key, model_file)
    
    # Extrai o conteúdo do arquivo tar.gz
    with tarfile.open(model_file, "r:gz") as t:
        t.extractall(path=".")
    
    # Carrega o modelo XGBoost
    model = xgb.Booster()
    model.load_model("xgboost-model")

    return model

def plot_roc_curve(fpr, tpr):
    """
    Plota a curva ROC e salva como uma imagem.

    Args:
        fpr (array): Taxa de falsos positivos.
        tpr (array): Taxa de verdadeiros positivos.

    Returns:
        str: Nome do arquivo da imagem salva.
    """
    # Define o nome do arquivo de saída
    fn = "roc-curve.png"
    
    # Cria uma nova figura
    fig = plt.figure(figsize=(6, 4))
    
    # Plota a linha diagonal 50%
    plt.plot([0, 1], [0, 1], 'k--')
    
    # Plota o FPR e TPR alcançados pelo modelo
    plt.plot(fpr, tpr)
    plt.xlabel('Taxa de Falsos Positivos')
    plt.ylabel('Taxa de Verdadeiros Positivos')
    plt.title('Curva ROC')
    
    # Salva a figura
    plt.savefig(fn)

    return fn
  
def evaluate(
    test_x_data_s3_path,
    test_y_data_s3_path,
    model_s3_path,
    output_s3_prefix,
    tracking_server_arn,
    experiment_name=None,
    pipeline_run_id=None,
    run_id=None,
):
    """
    Avalia um modelo XGBoost usando dados de teste e registra os resultados no MLflow.

    Args:
        test_x_data_s3_path (str): Caminho S3 para os dados de teste (features).
        test_y_data_s3_path (str): Caminho S3 para os dados de teste (labels).
        model_s3_path (str): Caminho S3 para o modelo treinado.
        output_s3_prefix (str): Prefixo S3 para armazenar os resultados.
        tracking_server_arn (str): ARN do servidor de rastreamento MLflow.
        experiment_name (str, opcional): Nome do experimento MLflow.
        pipeline_run_id (str, opcional): ID da execução do pipeline MLflow.
        run_id (str, opcional): ID da execução MLflow.

    Returns:
        dict: Resultados da avaliação e informações relacionadas.
    """
    try:
        # Gera um sufixo único baseado no tempo atual
        suffix = strftime('%d-%H-%M-%S', gmtime())
        
        # Configura o servidor de rastreamento MLflow
        mlflow.set_tracking_uri(tracking_server_arn)
        
        # Configura ou cria um experimento MLflow
        experiment = mlflow.set_experiment(experiment_name=experiment_name if experiment_name else f"{evaluate.__name__ }-{suffix}")
        
        # Inicia uma execução de pipeline MLflow, se fornecido um ID
        pipeline_run = mlflow.start_run(run_id=pipeline_run_id) if pipeline_run_id else None            
        
        # Inicia uma execução MLflow para esta avaliação
        run = mlflow.start_run(run_id=run_id) if run_id else mlflow.start_run(run_name=f"evaluate-{suffix}", nested=True)
        
        # Carrega os dados de teste
        X_test = xgb.DMatrix(pd.read_csv(test_x_data_s3_path, header=None).values)
        y_test = pd.read_csv(test_y_data_s3_path, header=None).to_numpy()
    
        # Carrega o modelo e faz previsões
        probability = load_model(model_s3_path).predict(X_test)
    
        # Calcula a curva ROC e o score AUC
        fpr, tpr, thresholds = roc_curve(y_test, probability)
        auc_score = auc(fpr, tpr)
        
        # Prepara os resultados da avaliação
        eval_result = {"evaluation_result": {
            "classification_metrics": {
                "auc_score": {
                    "value": auc_score,
                },
            },
        }}
        
        # Registra a métrica AUC no MLflow
        mlflow.log_metric("auc_score", auc_score)
        
        # Plota e registra a curva ROC no MLflow
        mlflow.log_artifact(plot_roc_curve(fpr, tpr))
        
        # Define o caminho S3 para a linha de base de previsão
        prediction_baseline_s3_path = f"{output_s3_prefix}/prediction_baseline/prediction_baseline.csv"
    
        # Salva a linha de base de previsão no S3
        pd.DataFrame({
            "prediction": np.array(np.round(probability), dtype=int),
            "probability": probability,
            "label": y_test.squeeze()
        }).to_csv(prediction_baseline_s3_path, index=False, header=True)
        
        # Retorna os resultados e informações relacionadas
        return {
            **eval_result,
            "prediction_baseline_data": prediction_baseline_s3_path,
            "experiment_name": experiment.name,
            "pipeline_run_id": pipeline_run.info.run_id if pipeline_run else ''
        }
            
    except Exception as e:
        print(f"Exceção no script de processamento: {e}")
        raise e
    finally:
        # Finaliza a execução MLflow
        mlflow.end_run()