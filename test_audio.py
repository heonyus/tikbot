#!/usr/bin/env python3
"""
Sound Alerts 시스템 테스트
"""

import asyncio
import logging
from src.tikbot.core.config import BotConfig
from src.tikbot.audio.manager import AudioManager

async def test_audio_system():
    """오디오 시스템 테스트"""
    print("🎵 Sound Alerts 시스템 테스트 시작...")
    
    # 설정 로드
    config = BotConfig.load_from_file()
    logger = logging.getLogger('test')
    logging.basicConfig(level=logging.INFO)
    
    # AudioManager 초기화
    audio_mgr = AudioManager(
        config=config.audio.model_dump(),
        logger=logger
    )
    
    success = await audio_mgr.initialize()
    print(f"✅ Audio Manager 초기화: {'SUCCESS' if success else 'FAILED'}")
    
    if success:
        # 통계 확인
        stats = audio_mgr.get_stats()
        print(f"📊 오디오 통계:")
        for key, value in stats.items():
            print(f"  - {key}: {value}")
        
        # 사용 가능한 사운드 파일 확인
        sounds = audio_mgr.list_available_sounds()
        print(f"🔊 사용 가능한 사운드: {len(sounds)}개")
        for sound in sounds:
            print(f"  - {sound['name']} ({sound['format']})")
    
    # 정리
    await audio_mgr.cleanup()
    print("🎵 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(test_audio_system())