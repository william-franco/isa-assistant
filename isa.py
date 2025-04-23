import os
import sys
import subprocess
import speech_recognition as sr
from gtts import gTTS
from playsound import playsound
import requests
from datetime import datetime
import psutil
import webbrowser as browser

def cria_audio(audio, mensagem, lang='pt-br'):
    tts = gTTS(mensagem, lang=lang)
    tts.save(audio)
    playsound(audio)
    os.remove(audio)

def monitora_audio():
    reconhecedor = sr.Recognizer()
    with sr.Microphone() as source:
        print("Estou ouvindo...")
        audio = reconhecedor.listen(source)
        try:
            mensagem = reconhecedor.recognize_google(audio, language='pt-BR')
            mensagem = mensagem.lower()
            print("Você disse:", mensagem)
            return mensagem
        except sr.UnknownValueError:
            cria_audio("erro.mp3", "Desculpe, não entendi.")
        except sr.RequestError:
            cria_audio("erro2.mp3", "Erro de conexão.")
    return ""

def obter_hora_brasil():
    try:
        url = "https://timeapi.io/api/Time/current/zone?timeZone=America/Sao_Paulo"
        response = requests.get(url)
        if response.status_code == 200:
            dados = response.json()
            hora_str = f"{dados['year']}-{dados['month']:02d}-{dados['day']:02d}T{dados['hour']:02d}:{dados['minute']:02d}:{dados['seconds']:02d}"
            hora = datetime.fromisoformat(hora_str)
            return hora
    except Exception as e:
        print("Erro ao obter hora:", e)
    return None

def ajustar_perfil_energia():
    uso_cpu = psutil.cpu_percent(interval=3)
    print(f"Uso médio de CPU: {uso_cpu}%")

    if uso_cpu < 30:
        perfil = 'power-saver'
    elif uso_cpu < 60:
        perfil = 'balanced'
    else:
        perfil = 'performance'

    try:
        subprocess.run(['powerprofilesctl', 'set', perfil], check=True)
        print(f"Perfil de energia ajustado para: {perfil}")
    except subprocess.CalledProcessError as e:
        print("Erro ao ajustar perfil de energia:", e)

def ajustar_brilho(hora):
    inicio_max = hora.replace(hour=10, minute=30, second=0, microsecond=0)
    fim_max = hora.replace(hour=16, minute=30, second=0, microsecond=0)

    if inicio_max <= hora <= fim_max:
        brilho = 100
    else:
        horas_diff = abs((hora - fim_max).seconds if hora > fim_max else (inicio_max - hora).seconds)
        horas = horas_diff // 3600
        brilho = max(20, 100 - horas * 10)
        brilho = brilho - (brilho % 2)

    try:
        subprocess.run(["brightnessctl", "set", f"{brilho}%"], check=True)
        print(f"Brilho ajustado para {brilho}%")
    except subprocess.CalledProcessError as e:
        print("Erro ao ajustar brilho:", e)

def abrir_programa(mensagem):
    programas = {
        "firefox": "firefox",
        "terminal": "gnome-terminal",
        "visual studio code": "code",
        "vscode": "code",
        "navegador": "firefox",
        "configurações": "gnome-control-center",
        "arquivos": "nautilus",
        "spotify": "spotify",
    }

    for nome, comando in programas.items():
        if nome in mensagem:
            cria_audio("abrindo.mp3", f"Abrindo {nome}")
            subprocess.Popen([comando])
            return

    cria_audio("naoencontrei.mp3", "Não encontrei o programa que você pediu.")

def executa_comandos(mensagem):
    if 'fechar assistente' in mensagem:
        cria_audio('desligando.mp3', 'Encerrando o assistente.')
        sys.exit()

    elif 'horas' in mensagem:
        hora = obter_hora_brasil()
        if hora:
            frase = f"Agora são {hora.strftime('%H:%M')}"
            cria_audio('horas.mp3', frase)

    elif 'desligar computador' in mensagem:
        if 'uma hora' in mensagem:
            os.system("shutdown -h +60")
        elif 'meia hora' in mensagem:
            os.system("shutdown -h +30")
        cria_audio('desligar.mp3', "Desligamento programado.")

    elif 'cancelar desligamento' in mensagem:
        os.system("shutdown -c")
        cria_audio('cancelado.mp3', "Desligamento cancelado.")

    elif 'pesquisar' in mensagem and 'google' in mensagem:
        pesquisa = mensagem.replace('pesquisar', '').replace('google', '').strip()
        cria_audio('pesquisa.mp3', f"Pesquisando por {pesquisa} no Google.")
        browser.open(f'https://www.google.com/search?q={pesquisa}')

    elif 'notícias' in mensagem:
        browser.open("https://g1.globo.com")
        cria_audio("noticias.mp3", "Abrindo as notícias mais recentes.")

    elif 'dólar' in mensagem:
        browser.open("https://www.google.com/search?q=cotação+dólar")
    elif 'euro' in mensagem:
        browser.open("https://www.google.com/search?q=cotação+euro")
    elif 'bitcoin' in mensagem:
        browser.open("https://www.google.com/search?q=cotação+bitcoin")

    else:
        abrir_programa(mensagem)

def main():
    hora = obter_hora_brasil()
    print(f"Hora atual: {hora}")
    if hora:
        ajustar_perfil_energia()
        ajustar_brilho(hora)
    else:
        print("Não foi possível obter a hora. Pulando ajustes.")

    cria_audio("inicio.mp3", "Olá! Sou a ISA. Como posso ajudar?")
    while True:
        comando = monitora_audio()
        if comando:
            executa_comandos(comando)

main()
