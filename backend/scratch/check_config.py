import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, Empresa
from app.utils_crypto import decrypt_key
from app.openai_client import gerar_audio
import tempfile

def test_tts():
    db = SessionLocal()
    empresas = db.query(Empresa).filter(Empresa.ativo == True).all()
    if not empresas:
        print("Nenhuma empresa ativa encontrada.")
        return

    for empresa in empresas:
        print(f"\n--- Empresa: {empresa.nome} (ID: {empresa.id}) ---")
        config = empresa.configuracoes.config if empresa.configuracoes else {}
        provedor_tts = config.get("provedor_tts", "openai")
        elevenlabs_voice_id = config.get("elevenlabs_voice_id")
        elevenlabs_api_key_encrypted = config.get("elevenlabs_api_key", "")
        elevenlabs_api_key = decrypt_key(elevenlabs_api_key_encrypted) if elevenlabs_api_key_encrypted else ""

        print(f"Provedor TTS configurado: {provedor_tts}")
        print(f"ElevenLabs Voice ID: {elevenlabs_voice_id}")
        print(f"ElevenLabs API Key configurada: {'Sim' if elevenlabs_api_key else 'Não'}")

        if provedor_tts == "elevenlabs":
            print("Testando geração de áudio com ElevenLabs...")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_out:
                caminho_audio_resposta = temp_out.name
            
            try:
                gerar_audio(
                    "Teste de áudio da ElevenLabs.", 
                    caminho_audio_resposta, 
                    provider=provedor_tts, 
                    voice=config.get("tts_voice", "nova"),
                    api_key=elevenlabs_api_key,
                    voice_id=elevenlabs_voice_id
                )
                size = os.path.getsize(caminho_audio_resposta)
                print(f"Áudio gerado com sucesso. Tamanho: {size} bytes")
            except Exception as e:
                print(f"Erro ao gerar áudio: {e}")
        else:
            print("Provedor não é elevenlabs, pulando teste de geração.")

    db.close()

if __name__ == "__main__":
    test_tts()
