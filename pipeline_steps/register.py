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
    """
    Registra um modelo treinado no SageMaker Model Registry e registra os metadados no MLflow.

    Args:
        training_job_name (str): Nome do job de treinamento do SageMaker.
        model_package_group_name (str): Nome do grupo de pacotes de modelo no SageMaker Model Registry.
        model_approval_status (str): Status de aprovação inicial do modelo ('Approved', 'PendingManualApproval', etc.).
        evaluation_result (dict): Resultados da avaliação do modelo.
        output_s3_prefix (str): Prefixo S3 para armazenar artefatos.
        tracking_server_arn (str): ARN do servidor de rastreamento MLflow.
        model_statistics_s3_path (str, opcional): Caminho S3 para estatísticas do modelo.
        model_constraints_s3_path (str, opcional): Caminho S3 para restrições do modelo.
        model_data_statistics_s3_path (str, opcional): Caminho S3 para estatísticas dos dados do modelo.
        model_data_constraints_s3_path (str, opcional): Caminho S3 para restrições dos dados do modelo.
        experiment_name (str, opcional): Nome do experimento MLflow.
        pipeline_run_id (str, opcional): ID da execução do pipeline MLflow.
        run_id (str, opcional): ID da execução MLflow.

    Returns:
        dict: Informações sobre o pacote de modelo registrado.
    """
    try:
        # Gera um sufixo único baseado no tempo atual
        suffix = strftime('%d-%H-%M-%S', gmtime())
        
        # Configura o servidor de rastreamento MLflow
        mlflow.set_tracking_uri(tracking_server_arn)
        
        # Configura ou cria um experimento MLflow
        experiment = mlflow.set_experiment(experiment_name=experiment_name if experiment_name else f"{register.__name__ }-{suffix}")
        
        # Inicia uma execução de pipeline MLflow, se fornecido um ID
        pipeline_run = mlflow.start_run(run_id=pipeline_run_id) if pipeline_run_id else None            
        
        # Inicia uma execução MLflow para este registro
        run = mlflow.start_run(run_id=run_id) if run_id else mlflow.start_run(run_name=f"register-{suffix}", nested=True)

        # Salva os resultados da avaliação em um arquivo JSON
        evaluation_result_path = f"evaluation.json"
        with open(evaluation_result_path, "w") as f:
            f.write(json.dumps(evaluation_result))
            
        # Registra o arquivo de avaliação como um artefato no MLflow
        mlflow.log_artifact(local_path=evaluation_result_path)
            
        # Anexa ao estimador do job de treinamento existente
        estimator = Estimator.attach(training_job_name)
        
        # Configura as métricas do modelo
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
    
        # Registra o modelo no SageMaker Model Registry
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

        # Registra os parâmetros do modelo no MLflow
        mlflow.log_params({
            "model_package_arn": model_package.model_package_arn,
            "model_statistics_uri": model_statistics_s3_path if model_statistics_s3_path else '',
            "model_constraints_uri": model_constraints_s3_path if model_constraints_s3_path else '',
            "data_statistics_uri": model_data_statistics_s3_path if model_data_statistics_s3_path else '',
            "data_constraints_uri": model_data_constraints_s3_path if model_data_constraints_s3_path else '',
        })

        # Retorna informações sobre o pacote de modelo registrado
        return {
            "model_package_arn": model_package.model_package_arn,
            "model_package_group_name": model_package_group_name,
            "pipeline_run_id": pipeline_run.info.run_id if pipeline_run else ''
        }

    except Exception as e:
        print(f"Exceção no script de processamento: {e}")
        raise e
    finally:
        # Finaliza a execução MLflow
        mlflow.end_run()