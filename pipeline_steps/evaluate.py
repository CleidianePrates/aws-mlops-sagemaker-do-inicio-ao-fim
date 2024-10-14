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

# função auxiliar para carregar o modelo XGBoost em xgboost.Booster
def load_model(model_data_s3_uri):
    model_file = "./xgboost-model.tar.gz"
    bucket, key = model_data_s3_uri.replace("s3://", "").split("/", 1)
    boto3.client("s3").download_file(bucket, key, model_file)
    
    with tarfile.open(model_file, "r:gz") as t:
        t.extractall(path=".")
    
    # Carregar modelo
    model = xgb.Booster()
    model.load_model("xgboost-model")

    return model

def plot_roc_curve(fpr, tpr):
    fn = "roc-curve.png"
    fig = plt.figure(figsize=(6, 4))
    
    # Plotar a linha diagonal 50%
    plt.plot([0, 1], [0, 1], 'k--')
    
    # Plotar o FPR e TPR alcançados pelo nosso modelo
    plt.plot(fpr, tpr)
    plt.xlabel('Taxa de Falsos Positivos')
    plt.ylabel('Taxa de Verdadeiros Positivos')
    plt.title('Curva ROC')
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
    try:
        suffix = strftime('%d-%H-%M-%S', gmtime())
        mlflow.set_tracking_uri(tracking_server_arn)
        experiment = mlflow.set_experiment(experiment_name=experiment_name if experiment_name else f"{evaluate.__name__ }-{suffix}")
        pipeline_run = mlflow.start_run(run_id=pipeline_run_id) if pipeline_run_id else None            
        run = mlflow.start_run(run_id=run_id) if run_id else mlflow.start_run(run_name=f"evaluate-{suffix}", nested=True)
        
        # Ler dados de teste
        X_test = xgb.DMatrix(pd.read_csv(test_x_data_s3_path, header=None).values)
        y_test = pd.read_csv(test_y_data_s3_path, header=None).to_numpy()
    
        # Executar previsões
        probability = load_model(model_s3_path).predict(X_test)
    
        # Avaliar previsões
        fpr, tpr, thresholds = roc_curve(y_test, probability)
        auc_score = auc(fpr, tpr)
        eval_result = {"evaluation_result": {
            "classification_metrics": {
                "auc_score": {
                    "value": auc_score,
                },
            },
        }}
        
        mlflow.log_metric("auc_score", auc_score)
        mlflow.log_artifact(plot_roc_curve(fpr, tpr))
        
        prediction_baseline_s3_path = f"{output_s3_prefix}/prediction_baseline/prediction_baseline.csv"
    
        # Salvar arquivo de linha de base de previsão - precisaremos dele posteriormente para o monitoramento da qualidade do modelo
        pd.DataFrame({"prediction":np.array(np.round(probability), dtype=int),
                      "probability":probability,
                      "label":y_test.squeeze()}
                    ).to_csv(prediction_baseline_s3_path, index=False, header=True)
        
        return {
            **eval_result,
            "prediction_baseline_data":prediction_baseline_s3_path,
            "experiment_name":experiment.name,
            "pipeline_run_id":pipeline_run.info.run_id if pipeline_run else ''
        }
            
    except Exception as e:
        print(f"Exceção no script de processamento: {e}")
        raise e
    finally:
        mlflow.end_run()


# Este código é usado para avaliar um modelo XGBoost e registrar métricas e artefatos no MLflow. 
# Aqui está o que cada função faz:

# - `load_model`: Esta função carrega um modelo XGBoost serializado a partir de um URI S3.
# - `plot_roc_curve`: Esta função plota a curva ROC (Receiver Operating Characteristic) e salva o gráfico 
# como um artefato PNG.
# - `evaluate`: Esta é a função principal que avalia o modelo XGBoost usando os dados de teste 
# fornecidos. Ela calcula a pontuação AUC (Area Under the Curve) e registra a métrica e o gráfico da curva ROC no MLflow. Além disso, 
# ela salva as previsões e probabilidades em um arquivo CSV chamado `prediction_baseline.csv` no prefixo S3 de saída fornecido. 
# O resultado da avaliação, incluindo a pontuação AUC, o caminho do arquivo de linha de base de previsão, o nome do experimento e 
# o ID da execução do pipeline, é retornado como um dicionário.

# O código usa as bibliotecas `numpy`, `pandas`, `xgboost`, `mlflow`, `sklearn`, `matplotlib`, `tarfile`, `pickle` e `boto3` para 
# carregar os dados, fazer previsões, avaliar o modelo, plotar a curva ROC e interagir com o MLflow e o Amazon S3.

