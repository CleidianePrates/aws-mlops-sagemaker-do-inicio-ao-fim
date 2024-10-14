import json
import sagemaker
import boto3
import mlflow
from time import gmtime, strftime
from sagemaker.estimator import Estimator
from sagemaker.model_metrics import (
    MetricsSource, 
    ModelMetrics, 
    FileSource
)

def register(
    training_job_name,
    model_package_group_name,
    model_approval_status,
    evaluation_result,
    output_s3_prefix,
    tracking_server_arn,
    model_statistics_s3_path=None,
    model_constraints_s3_path=None,
    model_data_statistics_s3_path=None,
    model_data_constraints_s3_path=None,
    experiment_name=None,
    pipeline_run_id=None,
    run_id=None,
):
    try:
        suffix = strftime('%d-%H-%M-%S', gmtime())
        mlflow.set_tracking_uri(tracking_server_arn)
        experiment = mlflow.set_experiment(experiment_name=experiment_name if experiment_name else f"{register.__name__ }-{suffix}")
        pipeline_run = mlflow.start_run(run_id=pipeline_run_id) if pipeline_run_id else None            
        run = mlflow.start_run(run_id=run_id) if run_id else mlflow.start_run(run_name=f"register-{suffix}", nested=True)

        evaluation_result_path = f"evaluation.json"
        with open(evaluation_result_path, "w") as f:
            f.write(json.dumps(evaluation_result))
            
        mlflow.log_artifact(local_path=evaluation_result_path)
            
        estimator = Estimator.attach(training_job_name)
        
        model_metrics = ModelMetrics(
            model_statistics=MetricsSource(
                s3_uri=model_statistics_s3_path,
                content_type="application/json",
            ) if model_statistics_s3_path else None,
            model_constraints=MetricsSource(
                s3_uri=model_constraints_s3_path,
                content_type="application/json",
            ) if model_constraints_s3_path else None,
            model_data_statistics=MetricsSource(
                s3_uri=model_data_statistics_s3_path,
                content_type="application/json",
            ) if model_data_statistics_s3_path else None,
            model_data_constraints=MetricsSource(
                s3_uri=model_data_constraints_s3_path,
                content_type="application/json",
            ) if model_data_constraints_s3_path else None,
        )
    
        model_package = estimator.register(
            content_types=["text/csv"],
            response_types=["text/csv"],
            inference_instances=["ml.m5.xlarge", "ml.m5.large"],
            transform_instances=["ml.m5.xlarge", "ml.m5.large"],
            model_package_group_name=model_package_group_name,
            approval_status=model_approval_status,
            model_metrics=model_metrics,
            model_name="from-idea-to-prod-pipeline-model",
            domain="MACHINE_LEARNING",
            task="CLASSIFICATION", 
        )

        mlflow.log_params({
            "model_package_arn":model_package.model_package_arn,
            "model_statistics_uri":model_statistics_s3_path if model_statistics_s3_path else '',
            "model_constraints_uri":model_constraints_s3_path if model_constraints_s3_path else '',
            "data_statistics_uri":model_data_statistics_s3_path if model_data_statistics_s3_path else '',
            "data_constraints_uri":model_data_constraints_s3_path if model_data_constraints_s3_path else '',
        })

        return {
            "model_package_arn":model_package.model_package_arn,
            "model_package_group_name":model_package_group_name,
            "pipeline_run_id":pipeline_run.info.run_id if pipeline_run else ''
        }

    except Exception as e:
        print(f"Exceção no script de processamento: {e}")
        raise e
    finally:
        mlflow.end_run()


# Este código é usado para registrar um modelo treinado como um pacote de modelo no Amazon SageMaker. 
# Aqui está o que a função `register` faz:

# 1. Configura o MLflow, definindo o URI de rastreamento e o experimento.
# 2. Salva o resultado da avaliação do modelo em um arquivo JSON local e registra-o como um artefato no MLflow.
# 3. Obtém o estimador do treinamento do modelo anexando-o ao nome do trabalho de treinamento fornecido.
# 4. Cria um objeto `ModelMetrics` a partir dos caminhos S3 fornecidos para as estatísticas do modelo, restrições do modelo, 
#     estatísticas dos dados do modelo e restrições dos dados do modelo.
# 5. Registra o modelo treinado como um pacote de modelo no Amazon SageMaker, fornecendo detalhes como tipos de conteúdo, 
#     tipos de resposta, instâncias de inferência e transformação, grupo do pacote de modelo, status de aprovação e métricas do modelo.
# 6. Registra os parâmetros relevantes no MLflow, incluindo o ARN do pacote de modelo, os URIs das estatísticas e restrições do modelo 
#     e dos dados.
# 7. Retorna um dicionário contendo o ARN do pacote de modelo, o nome do grupo do pacote de modelo e o ID da execução do pipeline (se aplicável).

# O código usa as bibliotecas `json`, `sagemaker`, `boto3`, `mlflow`, `sagemaker.estimator` e `sagemaker.model_metrics` para interagir 
# com o Amazon SageMaker e o MLflow.