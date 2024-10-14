import json
import random
import ast
import sys
import subprocess
import os

def preprocess_handler(inference_record):
    """
    Função para processar registros de inferência antes de serem utilizados pelo monitor de qualidade dos dados.

    :param inference_record: Objeto contendo os dados de entrada e saída da inferência e metadados associados.
    
    :return: Um dicionário representando os dados de entrada, onde as features são renomeadas para '_c0', '_c1', etc.
             Os dados de saída não são incluídos no registro para o monitor de qualidade dos dados.

    :raises ValueError: Se o tipo de codificação de entrada não for suportado.
    """

    input_enc_type = inference_record.endpoint_input.encoding  # Tipo de codificação dos dados de entrada
    input_data = inference_record.endpoint_input.data  # Dados de entrada da inferência
    output_data = inference_record.endpoint_output.data.rstrip("\n")  # Dados de saída da inferência
    eventmedatadata = inference_record.event_metadata  # Metadados do evento
    custom_attribute = json.loads(eventmedatadata.custom_attribute[0]) if eventmedatadata.custom_attribute is not None else None  # Atributos personalizados, se disponíveis

    if input_enc_type == "CSV":
        # Não incluir os dados de saída no registro para o monitor de qualidade dos dados
        outputs = input_data
        return { 
            f'_c{i}': float(d) if i in [0, 1, 2] else int(float(d)) for i, d in enumerate(outputs.split(","))
        }
    else:
        raise ValueError(f"O tipo de codificação {input_enc_type} não é suportado")  # Levanta erro para tipos de codificação não suportados

        
        

