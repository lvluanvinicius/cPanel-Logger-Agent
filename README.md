# Apache Logs Collector for WHM/cPanel

Este projeto é um agente de coleta de logs desenvolvido para receber e gerenciar logs do Apache gerados especificamente pelo WHM/cPanel. Ele foi projetado para rodar **fora do servidor WHM/cPanel**, recebendo os logs remotamente via **Syslog** na porta **514**. O agente é responsável por abrir a porta e gerenciar as conexões por meio de um socket dedicado.

## 🚀 Funcionalidades

- **Coleta Remota de Logs:** Recebe logs gerados pelo Apache no WHM/cPanel através do protocolo Syslog.
- **Compatibilidade Específica:** Projetado exclusivamente para lidar com os logs do WHM/cPanel.
- **Gerenciamento de Conexões:** Abre a porta 514 e gerencia conexões ativas utilizando sockets.
- **Processamento em Tempo Real:** Captura e processa logs à medida que são recebidos.
- **Armazenamento Flexível:** Opção de salvar os logs em arquivos locais ou encaminhar para sistemas de análise.
- **Segurança:** Isola o agente do servidor principal para maior segurança e desempenho.

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** [Informe a linguagem utilizada, como Python ou outra tecnologia].
- **Socket Programming:** Utiliza programação de sockets para escutar a porta 514 e gerenciar conexões Syslog.
- **Integração:** Compatível com ferramentas externas de análise de logs, como Elastic Stack (ELK) ou Splunk.

## 🖥️ Requisitos do Sistema

- **Servidor de Destino:** Um servidor separado, configurado para escutar e processar os logs enviados.
- **Porta 514 Aberta:** Certifique-se de que a porta 514 esteja aberta no firewall do servidor onde o script será executado.
- **Acesso ao WHM/cPanel:** Configuração no WHM/cPanel para encaminhar os logs ao endereço do servidor que executa este script.

## 📦 Instalação e Configuração

1. **Clone o Repositório:**
   ```bash
   git clone https://github.com/seu-usuario/apache-logs-collector.git
   cd apache-logs-collector
