# Esses comandos são fundamentais para gerenciar a infraestrutura do SageMaker em ambientes de trabalho usando CloudFormation, 
# permitindo implantar rapidamente um domínio e, se necessário, limpá-lo ao final do processo.

deploy-domain:
	aws cloudformation deploy \
    --template-file cfn-templates/sagemaker-domain.yaml \
    --stack-name sm-domain-workshop \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --parameter-overrides \
        DomainNamePrefix='sm-domain-projects-enabled'

destroy-domain:
	aws cloudformation delete-stack \
    --stack-name sm-domain-workshop && \
    aws cloudformation wait stack-delete-complete \
    --stack-name sm-domain-workshop

# deploy-domain:
# Este comando utiliza o AWS CloudFormation para implantar um domínio SageMaker:
# --template-file: Especifica o arquivo de template do CloudFormation que contém a definição do stack. No caso, sagemaker-domain.yaml.
# --stack-name: Nomeia a pilha do CloudFormation como sm-domain-workshop.
# --capabilities: Informa ao CloudFormation que a pilha pode criar ou atualizar funções IAM. Especifica duas capacidades: CAPABILITY_IAM e CAPABILITY_NAMED_IAM, que permitem o uso de funções IAM padrão e com nome.
# --parameter-overrides: Permite passar substituições de parâmetros para o template. Neste caso, DomainNamePrefix é definido como sm-domain-projects-enabled.



# destroy-domain:
# Este comando utiliza o AWS CloudFormation para deletar o domínio SageMaker:
# delete-stack: Deleta a pilha do CloudFormation especificada.
# --stack-name: Nomeia a pilha que deve ser deletada como sm-domain-workshop.
# &&: Operador lógico que garante que o próximo comando só seja executado se o comando anterior for bem-sucedido.
# wait stack-delete-complete: Aguarda até que a eliminação da pilha seja concluída, impedindo que outros processos interajam com o recurso até que esteja totalmente removido.