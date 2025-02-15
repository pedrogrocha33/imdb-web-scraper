"""
Este script extrai detalhes de filmes populares da IMDb.

Author: Bruno Medice edited by Pedro Rocha
Date: November 18, 2023
Update: January 31, 2024
"""
import time
import csv
import random
import concurrent.futures
import os
import threading
import requests
from bs4 import BeautifulSoup

# Header padrão usado na request
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) ' +
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

MAX_THREADS = 10

OUTPUT_DIRECTORY = './output'

# Bloqueio global para escrita no CSV
csv_lock = threading.Lock()

# Função para garantir nome único
def get_unique_filename(base_filename, directory):
    """
    Retorna um caminho de arquivo único no diretório especificado.

    Parameters:
    - base_filename (str): O nome base do arquivo.
    - directory (str): O diretório onde o arquivo deve ser salvo.
    """
    return os.path.join(directory, f"{base_filename}.csv")


def write_to_csv(output_file, data):
    """
    Escreve dados no arquivo CSV de forma segura usando um bloqueio.

    Parameters:
    - output_file (str): O caminho do arquivo CSV.
    - data (list): Lista de dados a serem escritos no arquivo.
    """
    with csv_lock:
        with open(output_file, mode='a', newline='', encoding='utf-8') as file:
            movie_writer = csv.writer(
                file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            movie_writer.writerow(data)
            
            


def extract_movie_details(movie_link, output_file):
    """
    Extrai detalhes de um filme do link fornecido e os escreve em um arquivo CSV.

    Parameters:
    - movie_link (str): O URL do filme.
    - output_file (str): O caminho do arquivo CSV para escrever os detalhes do filme.
    """
    time.sleep(random.uniform(0, 0.2))
    response = requests.get(movie_link, headers=headers, timeout=10)
    movie_soup = BeautifulSoup(response.content, 'html.parser')
    title, date, position, rating, summary = '', '', '', '', ''
    movie_data = movie_soup.find(
        'div', attrs={'class': 'sc-491663c0-3 bdjVSf'})
    # Encontrando e extraindo apenas o Summary
    if movie_data:
        # Extraindo informações do filme
        title = movie_data.find('h1').find(
            'span', attrs={'class': 'hero__primary-text'}).get_text()
        date = movie_data.find('a', attrs={
                               'class': 'ipc-link ipc-link--baseAlt ' +
                               'ipc-link--inherit-color'}).get_text().strip()
        position = movie_data.find(
            'div', attrs={'class': 'sc-5f7fb5b4-1 fTREEx'}).get_text()
        rating = movie_data.find(
            'span', attrs={'class': 'sc-bde20123-1 cMEQkK'}).get_text()
        # Extraindo o summary de uma outra parte do html
        summary = movie_soup.find(
        'span', attrs={'class': 'sc-eb5317c9-1 bpVsNr'}).get_text()

    # Verificando se todos os dados necessários estão disponíveis antes de gravar em CSV
    if all([position, title, date, rating, summary]):
        write_to_csv(output_file, [position, title, date, rating, summary])


def extract_movies(soup, output_directory):
    """
    Extrai links de filmes da página e inicia a execução paralela para extrair detalhes dos filmes.

    Parameters:
    - soup: O objeto BeautifulSoup da página web.
    - output_directory (str): O diretório de saída para os arquivos CSV.

    """
    movie_list = soup.findAll(
        'div', class_='sc-b189961a-0 hBZnfJ cli-children')
    
    # Verificando se a movie_list retornou vazia e caso positivo encerra script.
    if not movie_list:
        print_error_message_box("Nenhum filme encontrado.",
                                "Script será encerrado. Por favor, verifique as linhas correspondentes a extração dos filmes")
        return

    # Criando links para os filmes
    movie_links = ['https://imdb.com' +
                   movie.find('a')['href'] for movie in movie_list]

    # Definindo o arquivo de saída usando a função para garantir nome único
    output_file = get_unique_filename('movies', output_directory)

    # Iniciando a execução paralela para extrair detalhes dos filmes
    threads = min(MAX_THREADS, len(movie_links))
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(lambda link: extract_movie_details(
            link, output_file), movie_links)

def print_error_message_box(*messages):
    """
    Imprime uma mensagem de erro cercada por uma caixa de asteriscos com texto centralizado.

    Parameters:
     - message (str): A mensagem de erro a ser exibida.

    Example:
    >>> print_error_message_box("Nenhum filme encontrado. Script será encerrado. Por favor, verifique as linhas correspondentes a extração dos filmes")
    """
    max_length = max(len(message) for message in messages) + 6
    border_length = max_length + 6
    border = '*' * border_length
    line = '*' + ' ' * (border_length - 2) + '*'

    print('\n' + border)
    print(line)

    for message in messages:
        spaces_before = (border_length - len(message)-2) // 2
        spaces_after = border_length - len(message) - spaces_before - 2
        print(f'*{" " * spaces_before}{message}{" " * spaces_after}*')

    print(line)
    print(border + '\n')


def main():
    """
    Função principal para extrair dados de filmes populares do IMDb.
    """
    start_time = time.time()

    try:
        popular_movies_url = 'https://www.imdb.com/chart/moviemeter/?ref_=nv_mv_mpm'
        response = requests.get(
            popular_movies_url, headers=headers, timeout=10)

        # Check for network-related issues
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        output_directory = './output'
        os.makedirs(output_directory, exist_ok=True)

        extract_movies(soup, output_directory)

    except requests.exceptions.Timeout as e:
        print(f"Erro de timeout: {e}")
    except requests.exceptions.HTTPError as e:
        print(f"Erro HTTP: {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"Erro de conexão: {e}")
    except requests.exceptions.TooManyRedirects as e:
        print(f"Erro de redirecionamento excessivo: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Erro de requisição: {e}")
    # except bs4.FeatureNotFound as e:
    #    print(f"Erro de parsing HTML: {e}")
    except Exception as e:
        print(f"Um erro ocorreu: {e}")

    end_time = time.time()
    print(f'Tempo total gasto: {round(end_time - start_time)} segundos')

if __name__ == '__main__':
    main()
