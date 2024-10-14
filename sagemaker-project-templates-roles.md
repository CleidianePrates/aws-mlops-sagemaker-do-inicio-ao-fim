# Funções do Template de Projetos do Amazon SageMaker

Para usar os projetos do SageMaker fornecidos, você precisa provisionar funções de execução IAM específicas, conforme especificado em [Permissões do SageMaker Studio Necessárias para Usar Projetos](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-projects-studio-updates.html).

As seguintes funções são necessárias para usar os templates de projeto do SageMaker fornecidos:

- Função de restrição de lançamento: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsLaunchRole`
- Função de uso do produto: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsUseRole`
- Função de uso do CloudFormation: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsCloudformationRole`
- Função de uso do CodeBuild: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsCodeBuildRole`
- Função de uso do CodePipeline: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsCodePipelineRole`
- Função de uso de Eventos: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsEventsRole`
- Função de uso do API Gateway: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsApiGatewayRole`
- Função de uso do Firehose: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsFirehoseRole`
- Função de uso do Glue: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsGlueRole`
- Função de uso do Lambda: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsLambdaRole`
- Função de uso do SageMaker: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsExecutionRole`

## Provisionar as Funções Necessárias

Existem duas opções para provisionar as funções necessárias.

### Opção 1 - Console do SageMaker
Se você não tiver um domínio do SageMaker na sua conta, precisará criar um novo. Você deve habilitar todas as opções no painel **SageMaker Projects and JumpStart**:

![](img/enable-sagemaker-projects.png)

O domínio do SageMaker cria automaticamente as funções necessárias.

Se você já tiver um domínio do SageMaker em sua conta, siga as instruções de [Desligar e Atualizar o SageMaker Studio e Apps do Studio](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-tasks-update.html) para atualizar o domínio. Você deve desligar tanto os aplicativos JupyterServer quanto o KernelGateway. Após desligar todos os aplicativos, vá para o console do Amazon SageMaker, escolha **Domains** no painel à esquerda e selecione seu domínio. Vá para **Domain settings**, clique em **Configure app** no cartão **App**. Certifique-se de que todas as opções estejam habilitadas no painel **SageMaker Projects and JumpStart**. Clique em **Next** em todas as janelas de configuração e escolha **Submit**. Isso atualizará o domínio e criará automaticamente todas as funções de projeto necessárias.

### Opção 2 - usar o template do CloudFormation
Implante o template do CloudFormation fornecido [`cfn-templates/sagemaker-project-templates-roles.yaml`](cfn-templates/sagemaker-project-templates-roles.yaml). Para implantar as funções, você deve ter as permissões correspondentes para criar novas funções IAM.

Execute o seguinte comando no terminal de comando a partir do diretório do repositório do projeto:

```sh
aws cloudformation deploy \
    --template-file cfn-templates/sagemaker-project-templates-roles.yaml \
    --stack-name sagemaker-project-template-roles \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --parameter-overrides \
    CreateCloudFormationRole=YES \
    CreateCodeBuildRole=YES \
    CreateCodePipelineRole=YES \
    CreateEventsRole=YES \
    CreateProductsExecutionRole=YES 
```



## Aqui está a documentação para as funções do IAM necessárias para usar os projetos do Amazon SageMaker:

1. **Função de Restrições de Lançamento**: 
   - **ARN**: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsLaunchRole`
   - **Descrição**: Permite que o SageMaker inicie e gerencie os recursos necessários para os produtos do catálogo.

2. **Função de Uso do Produto**: 
   - **ARN**: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsUseRole`
   - **Descrição**: Permite que o SageMaker acesse e use os recursos provisionados pela implementação do projeto.

3. **Função de Uso do CloudFormation**: 
   - **ARN**: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsCloudformationRole`
   - **Descrição**: Permite que o SageMaker interaja com o AWS CloudFormation para gerenciar pilhas de recursos.

4. **Função de Uso do CodeBuild**: 
   - **ARN**: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsCodeBuildRole`
   - **Descrição**: Permite que o SageMaker execute trabalhos de construção e teste no AWS CodeBuild.

5. **Função de Uso do CodePipeline**: 
   - **ARN**: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsCodePipelineRole`
   - **Descrição**: Permite o gerenciamento de pipelines de integração e entrega contínua usando o AWS CodePipeline.

6. **Função de Uso de Eventos**: 
   - **ARN**: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsEventsRole`
   - **Descrição**: Permite que o SageMaker centralize e gerencie eventos relacionados ao serviço.

7. **Função de Uso do API Gateway**: 
   - **ARN**: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsApiGatewayRole`
   - **Descrição**: Permite a criação e gerenciamento de endpoints de API para interagir com os serviços do SageMaker.

8. **Função de Uso do Firehose**: 
   - **ARN**: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsFirehoseRole`
   - **Descrição**: Permite que o SageMaker envie dados para uma entrega contínua usando o Amazon Kinesis Data Firehose.

9. **Função de Uso do Glue**: 
   - **ARN**: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsGlueRole`
   - **Descrição**: Permite que o SageMaker execute tarefas de ETL (extração, transformação e carga) usando o AWS Glue.

10. **Função de Uso do Lambda**: 
    - **ARN**: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsLambdaRole`
    - **Descrição**: Permite que o SageMaker execute funções do AWS Lambda como parte do fluxo de trabalho do projeto.

11. **Função de Uso do SageMaker**: 
    - **ARN**: `arn:aws:iam:::role/service-role/AmazonSageMakerServiceCatalogProductsExecutionRole`
    - **Descrição**: A função principal que permite ao SageMaker executar modelos e interagir com outros serviços AWS durante o processamento do projeto.

Estas funções IAM são essenciais para o funcionamento correto e seguro dos projetos do SageMaker, garantindo que os recursos necessários possam ser criados, acessados e gerenciados de forma apropriada.