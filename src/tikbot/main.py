"""
TikBot 메인 엔트리포인트
"""

import asyncio
import signal
import sys
from pathlib import Path
from typing import Optional

import colorlog
import uvicorn
from dotenv import load_dotenv

from .core.bot import TikBot
from .core.config import BotConfig
from .api.server import create_app


def setup_logging():
    """로깅 설정"""
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    ))
    
    logger = colorlog.getLogger('tikbot')
    logger.addHandler(handler)
    logger.setLevel('INFO')
    return logger


async def run_bot(config: BotConfig, logger):
    """봇 실행"""
    bot = TikBot(config, logger)
    
    def signal_handler(signum, frame):
        logger.info("종료 신호를 받았습니다. 봇을 정리하는 중...")
        asyncio.create_task(bot.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await bot.start()
        logger.info("TikBot이 성공적으로 시작되었습니다!")
        
        # 봇이 실행 중일 때까지 대기
        while bot.is_running:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"봇 실행 중 오류 발생: {e}")
        await bot.stop()
    finally:
        logger.info("TikBot이 종료되었습니다.")


async def run_with_api(config: BotConfig, logger):
    """봇과 API 서버를 함께 실행"""
    # FastAPI 앱 생성
    app = create_app(config, logger)
    
    # 봇 인스턴스 생성
    bot = TikBot(config, logger)
    app.state.bot = bot
    
    # 봇 시작
    await bot.start()
    logger.info("TikBot과 API 서버를 시작합니다...")
    
    # API 서버 실행
    server_config = uvicorn.Config(
        app,
        host=config.api.host,
        port=config.api.port,
        log_level="info"
    )
    server = uvicorn.Server(server_config)
    
    try:
        await server.serve()
    finally:
        await bot.stop()


def main():
    """메인 함수"""
    # 환경 변수 로드
    load_dotenv()
    
    # 로깅 설정
    logger = setup_logging()
    
    # 설정 로드
    try:
        config = BotConfig.load_from_file()
        logger.info(f"설정 로드 완료: {config.tiktok.username}")
    except Exception as e:
        logger.error(f"설정 로드 실패: {e}")
        logger.info("기본 설정으로 config.yaml 파일을 생성합니다...")
        config = BotConfig()
        config.save_to_file()
        logger.info("config.yaml을 편집한 후 다시 실행해주세요.")
        return
    
    # 실행 모드 선택
    if len(sys.argv) > 1 and sys.argv[1] == "--api":
        # API 서버와 함께 실행
        asyncio.run(run_with_api(config, logger))
    else:
        # 봇만 실행
        asyncio.run(run_bot(config, logger))


if __name__ == "__main__":
    main()