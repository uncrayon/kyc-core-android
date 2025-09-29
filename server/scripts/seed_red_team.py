#!/usr/bin/env python3
"""
Red Team Dataset Seeder for KYC Fraud Detection

This script injects 60-80 test videos representing various presentation attacks:
- Print attacks (photos, documents)
- Replay attacks (screen recordings)
- Mask attacks (face coverings)
- Fake documents (forged IDs)

Usage: python scripts/seed_red_team.py
"""

import os
import random
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.orm import sessionmaker
from db.database import engine, SessionLocal
from db.models import KycSession, PadResult, DeepfakeResult, FaceMatchResult, OcrResult, MrzResult, DocLivenessResult, RiskScore

# Mock video data - in real implementation, these would be actual video files
ATTACK_TYPES = {
    'print_attack': {
        'description': 'Printed photo or document attack',
        'count': 20,
        'variations': ['photo_print', 'document_print', 'high_quality_print', 'low_quality_print']
    },
    'replay_attack': {
        'description': 'Screen or video replay attack',
        'count': 20,
        'variations': ['screen_replay', 'video_replay', 'looped_replay', 'compressed_replay']
    },
    'mask_attack': {
        'description': 'Face mask or covering attack',
        'count': 15,
        'variations': ['surgical_mask', 'n95_mask', 'cloth_mask', 'face_paint', 'prosthetic_mask']
    },
    'fake_document': {
        'description': 'Forged or manipulated document',
        'count': 15,
        'variations': ['photoshopped_id', 'scanned_fake', 'tampered_mrz', 'wrong_template']
    },
    'deepfake': {
        'description': 'AI-generated deepfake video',
        'count': 10,
        'variations': ['face_swap', 'expression_manip', 'voice_sync', 'full_deepfake']
    }
}

def generate_mock_video_data(attack_type: str, variation: str, index: int) -> dict:
    """Generate mock video metadata for testing"""
    session_id = str(uuid.uuid4())
    timestamp = datetime.now() - timedelta(days=random.randint(0, 30))

    return {
        'session_id': session_id,
        'attack_type': attack_type,
        'variation': variation,
        'video_path': f'red_team_videos/{attack_type}/{variation}_{index:03d}.mp4',
        'metadata': {
            'duration_seconds': random.uniform(5.0, 30.0),
            'frame_rate': random.choice([15, 24, 30, 60]),
            'resolution': random.choice(['720p', '1080p', '4K']),
            'bitrate_kbps': random.randint(500, 5000),
            'codec': random.choice(['H.264', 'H.265', 'VP9']),
            'file_size_mb': random.uniform(1.0, 50.0)
        },
        'expected_pad_score': random.uniform(0.0, 0.3),  # Low scores for attacks
        'timestamp': timestamp.isoformat(),
        'device_info': {
            'user_agent': f'MockDevice/{random.randint(1, 10)}',
            'platform': random.choice(['Android', 'iOS']),
            'app_version': f'1.{random.randint(0, 5)}.{random.randint(0, 9)}'
        },
        'labels': {
            'is_attack': True,
            'attack_category': attack_type,
            'difficulty_level': random.choice(['easy', 'medium', 'hard']),
            'detection_confidence': random.uniform(0.7, 0.95)
        }
    }

def create_directory_structure(base_path: str):
    """Create directory structure for red team videos"""
    for attack_type in ATTACK_TYPES.keys():
        attack_dir = Path(base_path) / attack_type
        attack_dir.mkdir(parents=True, exist_ok=True)

        # Create variation subdirectories
        for variation in ATTACK_TYPES[attack_type]['variations']:
            var_dir = attack_dir / variation
            var_dir.mkdir(exist_ok=True)

def seed_red_team_dataset(video_base_path: str = 'red_team_videos'):
    """Main function to seed the red team dataset into database"""

    print("🔴 Starting Red Team Dataset Seeding...")
    print(f"Target: {sum(config['count'] for config in ATTACK_TYPES.values())} test sessions")

    # Create directory structure
    create_directory_structure(video_base_path)

    db = SessionLocal()
    total_created = 0

    try:
        for attack_type, config in ATTACK_TYPES.items():
            print(f"\n📁 Processing {attack_type}: {config['description']}")

            videos_created = 0
            for variation in config['variations']:
                variation_count = config['count'] // len(config['variations'])
                if videos_created < config['count']:
                    remaining = config['count'] - videos_created
                    variation_count = min(variation_count, remaining)

                for i in range(variation_count):
                    video_data = generate_mock_video_data(attack_type, variation, total_created)

                    # Create KycSession
                    session = KycSession(
                        session_id=video_data['session_id'],
                        selfie_video_path=video_data['video_path'],
                        id_video_path=video_data['video_path'],  # Same for simplicity
                        status='completed'
                    )
                    db.add(session)
                    db.flush()  # To get session.id

                    # Create mock results
                    pad_result = PadResult(
                        session_id=session.id,
                        score=video_data['expected_pad_score'],
                        threshold=0.5,
                        passed=1 if video_data['expected_pad_score'] < 0.5 else 0,
                        details={'attack_type': attack_type, 'variation': variation}
                    )
                    db.add(pad_result)

                    deepfake_result = DeepfakeResult(
                        session_id=session.id,
                        score=random.uniform(0.0, 0.3),
                        threshold=0.5,
                        passed=1,
                        details={'attack_type': attack_type}
                    )
                    db.add(deepfake_result)

                    face_match_result = FaceMatchResult(
                        session_id=session.id,
                        cosine_similarity=random.uniform(0.1, 0.9),
                        threshold=0.7,
                        passed=0,  # Attacks should fail
                        details={'attack_type': attack_type}
                    )
                    db.add(face_match_result)

                    ocr_result = OcrResult(
                        session_id=session.id,
                        extracted_text='MOCK TEXT',
                        confidence=random.uniform(0.5, 0.9),
                        document_type='ID',
                        details={}
                    )
                    db.add(ocr_result)

                    mrz_result = MrzResult(
                        session_id=session.id,
                        mrz_data={'raw': 'MOCK MRZ'},
                        parsed_fields={'name': 'MOCK NAME'},
                        valid=1,
                        details={}
                    )
                    db.add(mrz_result)

                    doc_liveness_result = DocLivenessResult(
                        session_id=session.id,
                        score=random.uniform(0.0, 0.4),
                        threshold=0.5,
                        passed=0,  # Attacks should fail
                        details={'attack_type': attack_type}
                    )
                    db.add(doc_liveness_result)

                    risk_score = RiskScore(
                        session_id=session.id,
                        overall_score=random.uniform(0.7, 1.0),
                        risk_level='high',
                        component_scores={'pad': pad_result.score, 'face_match': face_match_result.cosine_similarity},
                        weights={'pad': 0.4, 'face_match': 0.6},
                        decision='reject'
                    )
                    db.add(risk_score)

                    # Create mock video file
                    video_path = Path(video_base_path) / attack_type / variation / f"{variation}_{total_created:03d}.mp4"
                    video_path.touch()

                    total_created += 1
                    videos_created += 1

                    if total_created % 10 == 0:
                        print(f"  ✓ Created {total_created} sessions...")

            print(f"  ✓ Completed {attack_type}: {videos_created} sessions")

        db.commit()

        print("\n✅ Red Team Dataset Seeding Complete!")
        print(f"📊 Total sessions created: {total_created}")
        print(f"📁 Videos stored in: {video_base_path}/")

        # Print summary by attack type
        print("\n📈 Attack Type Summary:")
        for attack_type, config in ATTACK_TYPES.items():
            count = db.query(KycSession).join(PadResult).filter(PadResult.details['attack_type'].astext == attack_type).count()
            print(f"  {attack_type}: {count} sessions")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        db.close()

    return total_created

if __name__ == '__main__':
    # Ensure we're in the server directory
    os.chdir(Path(__file__).parent.parent)

    seed_red_team_dataset()