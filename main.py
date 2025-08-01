import socket
import pymongo
import re
import os
from datetime import datetime
from multiprocessing import Process, Queue
import logging
from dotenv import load_dotenv
from queue import Empty

load_dotenv()

# Configuração básica do logger
logging.basicConfig(
    filename='/home/cednet/cpanel_logs/logs/main.log',  # Caminho do arquivo de log
    level=logging.DEBUG,              # Nível do log
    format='%(asctime)s - %(levelname)s - %(message)s'  # Formato da mensagem
)

# Configuração do banco de dados MongoDB
mongo_config = {
    'uri': os.getenv('MONGO_URI', 'mongodb://localhost:27017/cpanel_logs'),
    'db_name': os.getenv('MONGO_DB_NAME', 'cpanel_logs'), # Pode ser sobrescrito pela URI
    'collection_name': os.getenv('MONGO_COLLECTION_NAME', 'access_logs'),
}

# Configurar o socket UDP.
UDP_IP = "0.0.0.0"
UDP_PORT = 514
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# Regex para processar os logs (ajuste conforme necessário).
pattern = r'^(?P<date>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(?P<hostname>\S+)\s+(?P<server_tag>\S+)\s+(?P<ip_address>\d+\.\d+\.\d+\.\d+)\s+-\s+(?P<user>\S+)\s+\[(?P<timestamp>[^\]]+)\]\s+"(?P<method>\S+)\s+(?P<url>\S+)\s+HTTP/\d\.\d"\s+(?P<status_code>\d+)\s+(?P<response_size>\d+)\s+"(?P<referrer>[^"]+)"\s+"(?P<user_agent>[^"]+)"\s+"(?P<unknown_field>[^"]+)"\s+"(?P<extra_field>[^"]+)"\s+(?P<port>\d+)'

def clean_log_message(log_message):
    # Remover o código de prioridade syslog, como <190>
    clean_message = re.sub(r'<\d+>', '', log_message)
    return clean_message

def parse_log_line(line):
    """Parse a line of log, extracting the necessary information"""
    try:
        line_string = clean_log_message(line)
        match = re.match(pattern, line_string)
        if match:
            log_data = match.groupdict()
            # Convertendo 'timestamp' para datetime para facilitar manipulação futura
            log_data['timestamp'] = datetime.strptime(log_data['timestamp'], '%m/%d/%Y:%H:%M:%S %z')
            return log_data
    except Exception as e:
        logging.error(f"Erro ao parsear linha: {e}")
    return None

def connect_to_mongodb():
    """Tenta conectar ao MongoDB e retorna o cliente e a coleção."""
    try:
        client = pymongo.MongoClient(mongo_config['uri'])
        db = client[mongo_config['db_name']]
        collection = db[mongo_config['collection_name']]
        logging.info("Conectado ao MongoDB.")
        return client, collection
    except pymongo.errors.ConnectionFailure as e:
        logging.error(f"Falha ao conectar ao MongoDB: {e}", exc_info=True)
        return None, None

def insert_logs_to_db(log_queue):
    """Subprocesso que consome logs da fila e insere no banco de dados."""
    client, collection = connect_to_mongodb()
    if not client:
        logging.error("Não foi possível conectar ao MongoDB. Encerrando subprocesso.")
        return

    while True:
        try:
            # Buscar logs na fila com timeout
            logs = log_queue.get(timeout=10)
            if logs is None:  # Sinal para encerrar o subprocesso
                break

            if not logs:
                continue

            # Inserir os logs no MongoDB
            collection.insert_many(logs)
            logging.info(f"{len(logs)} logs inseridos no MongoDB.")

        except pymongo.errors.PyMongoError as e:
            logging.error(f"Erro no MongoDB: {e}", exc_info=True)
            # Tentar reconectar ao banco
            client, collection = connect_to_mongodb()
            if not client:
                logging.error("Reconexão ao MongoDB falhou. Encerrando subprocesso.")
                break  # Encerra o subprocesso se não for possível reconectar
        except Empty:
            logging.debug("Nenhum log disponível na fila dentro do timeout.")
        except Exception as e:
            logging.error(f"Erro inesperado no subprocesso de inserção: {e}", exc_info=True)

    if client:
        client.close()
        logging.info("Conexão com MongoDB encerrada.")

def main():
    """Função principal para receber logs e enviar para o subprocesso."""
    logging.info(f"Aguardando logs na porta {UDP_PORT}...")
    log_queue = Queue()
    process = Process(target=insert_logs_to_db, args=(log_queue,))
    process.start()

    logs_batch = []
    batch_size = 100

    sock.settimeout(10)  # Timeout para o socket

    try:
        while True:
            try:
                # Receber dados do socket
                data, addr = sock.recvfrom(2048)
                log_message = data.decode('utf-8', errors='ignore')
                parsed = parse_log_line(log_message)

                if parsed:
                    # Adicionar o ano ao valor de parsed['date']
                    log_date_str = parsed['date']  # Formato: "Nov 21 15:55:12"
                    current_year = datetime.now().year  # Obter o ano atual
                    parsed['date'] = f"{log_date_str} {current_year}"  # Adicionar o ano

                    # Adicionar ao batch
                    logs_batch.append(parsed)

                # Enviar lote de logs para a fila
                if len(logs_batch) >= batch_size:
                    log_queue.put(logs_batch)
                    logs_batch = []

            except socket.timeout:
                logging.warning("Timeout ao receber dados no socket.")
            except Exception as e:
                logging.error(f"Erro ao processar log: {e}", exc_info=True)

    except KeyboardInterrupt:
        logging.info("Encerrando servidor UDP.")
    finally:
        # Enviar sinal para finalizar o subprocesso
        log_queue.put(None)
        process.join()
        sock.close()
        logging.info("Conexão UDP encerrada.")


if __name__ == '__main__':
    main()