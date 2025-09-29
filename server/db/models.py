from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class KycSession(Base):
    __tablename__ = 'kyc_sessions'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    selfie_video_path = Column(String)
    id_video_path = Column(String)
    status = Column(String, default='pending')  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    frame_extraction = relationship("FrameExtraction", back_populates="session", uselist=False)
    pad_result = relationship("PadResult", back_populates="session", uselist=False)
    deepfake_result = relationship("DeepfakeResult", back_populates="session", uselist=False)
    face_match_result = relationship("FaceMatchResult", back_populates="session", uselist=False)
    ocr_result = relationship("OcrResult", back_populates="session", uselist=False)
    mrz_result = relationship("MrzResult", back_populates="session", uselist=False)
    doc_liveness_result = relationship("DocLivenessResult", back_populates="session", uselist=False)
    risk_score = relationship("RiskScore", back_populates="session", uselist=False)

class FrameExtraction(Base):
    __tablename__ = 'frame_extractions'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('kyc_sessions.id'))
    frames_path = Column(String)  # Path to extracted frames
    frame_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("KycSession", back_populates="frame_extraction")

class PadResult(Base):
    __tablename__ = 'pad_results'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('kyc_sessions.id'))
    score = Column(Float)
    threshold = Column(Float)
    passed = Column(Integer)  # 1 for pass, 0 for fail
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("KycSession", back_populates="pad_result")

class DeepfakeResult(Base):
    __tablename__ = 'deepfake_results'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('kyc_sessions.id'))
    score = Column(Float)
    threshold = Column(Float)
    passed = Column(Integer)  # 1 for pass, 0 for fail
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("KycSession", back_populates="deepfake_result")

class FaceMatchResult(Base):
    __tablename__ = 'face_match_results'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('kyc_sessions.id'))
    cosine_similarity = Column(Float)
    threshold = Column(Float)
    passed = Column(Integer)  # 1 for pass, 0 for fail
    face_image_path = Column(String)
    id_photo_path = Column(String)
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("KycSession", back_populates="face_match_result")

class OcrResult(Base):
    __tablename__ = 'ocr_results'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('kyc_sessions.id'))
    extracted_text = Column(String)
    confidence = Column(Float)
    document_type = Column(String)
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("KycSession", back_populates="ocr_result")

class MrzResult(Base):
    __tablename__ = 'mrz_results'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('kyc_sessions.id'))
    mrz_data = Column(JSON)
    parsed_fields = Column(JSON)
    valid = Column(Integer)  # 1 for valid, 0 for invalid
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("KycSession", back_populates="mrz_result")

class DocLivenessResult(Base):
    __tablename__ = 'doc_liveness_results'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('kyc_sessions.id'))
    score = Column(Float)
    threshold = Column(Float)
    passed = Column(Integer)  # 1 for pass, 0 for fail
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("KycSession", back_populates="doc_liveness_result")

class RiskScore(Base):
    __tablename__ = 'risk_scores'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('kyc_sessions.id'))
    overall_score = Column(Float)
    risk_level = Column(String)  # low, medium, high
    component_scores = Column(JSON)  # Individual scores from each service
    weights = Column(JSON)  # Weights used for calculation
    decision = Column(String)  # approve, reject, manual_review
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("KycSession", back_populates="risk_score")