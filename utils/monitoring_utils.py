# Importa os módulos necessários
import os, sys
from urllib.parse import urlparse
from sagemaker.processing import Processor, ProcessingInput, ProcessingOutput

# Função para obter o URI do contêiner do Amazon SageMaker Model Monitor com base na região
def get_model_monitor_container_uri(region):
    # Formato do URI do contêiner
    container_uri_format = '{0}.dkr.ecr.{1}.amazonaws.com/sagemaker-model-monitor-analyzer'
    
    # Dicionário que mapeia as regiões para as contas da AWS
    regions_to_accounts = {
        'eu-north-1': '895015795356',
        # ... (outras regiões omitidas para brevidade)
    }
    
    # Constrói o URI do contêiner usando a região e a conta da AWS
    container_uri = container_uri_format.format(regions_to_accounts[region], region)
    return container_uri

# Função para obter o nome do arquivo a partir de uma URL
def get_file_name(url):
    a = urlparse(url)
    return os.path.basename(a.path)

# Função principal para executar o trabalho de monitoramento de modelo
def run_model_monitor_job(
    region,
    instance_type,
    role,
    data_capture_path,
    statistics_path,
    constraints_path,
    reports_path,
    instance_count=1,
    preprocessor_path=None,
    postprocessor_path=None,
    publish_cloudwatch_metrics='Disabled',
    wait=True,
    logs=True,
):
    
    # Obter o subdiretório da captura de dados a partir do caminho
    data_capture_sub_path = data_capture_path[data_capture_path.rfind('datacapture') :]
    data_capture_sub_path = data_capture_sub_path[data_capture_sub_path.find('/') + 1 :]
    processing_output_paths = reports_path + '/' + data_capture_sub_path
    
    # Definir as entradas de processamento
    input_1 = ProcessingInput(input_name='input_1',
                              source=data_capture_path,
                              destination='/opt/ml/processing/input/endpoint/' + data_capture_sub_path,
                              s3_data_type='S3Prefix',
                              s3_input_mode='File')

    baseline = ProcessingInput(input_name='baseline',
                               source=statistics_path,
                               destination='/opt/ml/processing/baseline/stats',
                               s3_data_type='S3Prefix',
                               s3_input_mode='File')

    constraints = ProcessingInput(input_name='constraints',
                                  source=constraints_path,
                                  destination='/opt/ml/processing/baseline/constraints',
                                  s3_data_type='S3Prefix',
                                  s3_input_mode='File')

    # Definir a saída de processamento
    outputs = ProcessingOutput(output_name='result',
                               source='/opt/ml/processing/output',
                               destination=processing_output_paths,
                               s3_upload_mode='Continuous')

    # Definir as variáveis de ambiente para o contêiner
    env = {'baseline_constraints': '/opt/ml/processing/baseline/constraints/' + get_file_name(constraints_path),
           'baseline_statistics': '/opt/ml/processing/baseline/stats/' + get_file_name(statistics_path),
           'dataset_format': '{"sagemakerCaptureJson":{"captureIndexNames":["endpointInput","endpointOutput"]}}',
           'dataset_source': '/opt/ml/processing/input/endpoint',
           'output_path': '/opt/ml/processing/output',
           'publish_cloudwatch_metrics': publish_cloudwatch_metrics }
    
    inputs = [input_1, baseline, constraints]
    
    # Se um caminho para o pós-processador for fornecido, adicione-o às entradas e variáveis de ambiente
    if postprocessor_path:
        env['post_analytics_processor_script'] = '/opt/ml/processing/code/postprocessing/' + get_file_name(postprocessor_path)
        
        post_processor_script = ProcessingInput(input_name='post_processor_script',
                                                source=postprocessor_path,
                                                destination='/opt/ml/processing/code/postprocessing',
                                                s3_data_type='S3Prefix',
                                                s3_input_mode='File')
        inputs.append(post_processor_script)

    # Se um caminho para o pré-processador for fornecido, adicione-o às entradas e variáveis de ambiente
    if preprocessor_path:
        env['record_preprocessor_script'] = '/opt/ml/processing/code/preprocessing/' + get_file_name(preprocessor_path)
         
        pre_processor_script = ProcessingInput(input_name='pre_processor_script',
                                               source=preprocessor_path,
                                               destination='/opt/ml/processing/code/preprocessing',
                                               s3_data_type='S3Prefix',
                                               s3_input_mode='File')
        
        inputs.append(pre_processor_script) 
    
    # Criar o objeto Processor
    processor = Processor(image_uri=get_model_monitor_container_uri(region),
                          instance_count=instance_count,
                          instance_type=instance_type,
                          role=role,
                          env=env)

    # Executar o trabalho de processamento
    return processor.run(inputs=inputs, 
                         outputs=[outputs],
                         wait=wait,
                         logs=logs,
                        )

# Esse código é usado para executar um trabalho de monitoramento de modelo no Amazon SageMaker. Ele define as entradas 
# necessárias, como os dados de captura do endpoint, estatísticas de referência e restrições, bem como as saídas esperadas. 
# Também configura as variáveis de ambiente necessárias para o contêiner do Amazon SageMaker Model Monitor.

# A função `get_model_monitor_container_uri` retorna o URI do contêiner do Amazon SageMaker Model Monitor com base na região 
# fornecida. A função `get_file_name` é uma função auxiliar que extrai o nome do arquivo de uma URL.

# A função principal `run_model_monitor_job` é responsável por configurar e executar o trabalho de monitoramento de modelo. 
# Ela aceita vários parâmetros, como a região, o tipo de instância, a função do IAM, os caminhos para os dados de captura, 
# estatísticas de referência, restrições e relatórios. Opcionalmente, também é possível fornecer caminhos para scripts de 
# pré-processamento e pós-processamento.

# O código cria objetos `ProcessingInput` e `ProcessingOutput` para definir as entradas e saídas do trabalho de processamento. 
# Em seguida, configura as variáveis de ambiente necessárias e cria um objeto `Processor` usando o URI do contêiner do Amazon 
# SageMaker Model Monitor. Por fim, executa o trabalho de processamento chamando o método `run` do objeto `Processor`.