from typing import List, Optional
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.entity.shorts import Shorts
from app.entity.user import User
from app.exceptions.http_exceptions import ServerException
from app.models.schemas import ShortsScript, ShortsScriptUpsertRequest
from sqlalchemy import func
from app.services.google_ai_service import GoogleAIService

google_ai_service = GoogleAIService()


class ShortScriptService:
    def __init__(self):
        pass

    def get_script(self, session: Session, user_id: int, script_id: int) -> Optional[ShortsScript]:
        statement = select(Shorts).where(Shorts.id == script_id, Shorts.user_id == user_id, Shorts.status != "DELETED")
        result = session.exec(statement).first()

        if not result:
            return None

        script = ShortsScript(**result.shorts_json)
        script.id = result.id
        script.title = result.title
        script.created_at = result.created_at
        script.updated_at = result.updated_at
        return script

    def get_all_scripts(self, session: Session, user_id: int) -> list[ShortsScript]:
        statement = (
            select(Shorts)
            .where(Shorts.user_id == user_id, Shorts.status != "DELETED")
            .order_by(Shorts.updated_at.desc())
        )
        results = session.exec(statement).all()
        scripts = []
        deleted_scripts_ids = []
        for result in results:
            if datetime.now() > result.created_at + timedelta(days=2):
                deleted_scripts_ids.append(result.id)
                continue

            script = ShortsScript(**result.shorts_json)
            script.id = result.id
            script.title = result.title
            script.created_at = result.created_at
            script.updated_at = result.updated_at
            scripts.append(script)

        if len(deleted_scripts_ids) > 0:
            statement = select(Shorts).where(Shorts.id.in_(deleted_scripts_ids), Shorts.user_id == user_id)
            results = session.exec(statement).all()

            if not results:
                return False

            try:
                for result in results:
                    result.status = "DELETED"
                    session.add(result)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                raise ServerException("스크립트 만료 처리 중 오류가 발생했습니다.", data=str(e))

        return scripts

    def delete_script(self, session: Session, user_id: int, script_id: int) -> bool:
        statement = select(Shorts).where(Shorts.id == script_id, Shorts.user_id == user_id)
        result = session.exec(statement).first()

        if not result:
            return False

        try:
            result.status = "DELETED"
            session.add(result)
            session.commit()
            session.refresh(result)
            return True
        except Exception as e:
            session.rollback()
            raise ServerException("스크립트 삭제 중 오류가 발생했습니다.", data=str(e))

    async def upsert_script(self, session: Session, user_id: int, request: ShortsScriptUpsertRequest):
        if request.id > 0:
            statement = select(Shorts).where(Shorts.id == int(request.id), Shorts.user_id == user_id)
            result = session.exec(statement).first()

            if result:
                if result.created_at < datetime.now() - timedelta(days=2):
                    result.status = "DELETED"
                    session.add(result)
                    session.commit()
                    session.refresh(result)
                    raise ServerException("스크립트가 만료되어 새로 생성해야 합니다.")

                result.title = request.title or await google_ai_service.summarize_text(
                    " ".join([scene.description or "" for scene in request.shorts_json.scenes])
                )
                result.shorts_json = request.shorts_json.model_dump()
                result.updated_at = datetime.now()

                try:
                    session.add(result)
                    session.commit()
                    session.refresh(result)
                except Exception as e:
                    session.rollback()
                    raise ServerException("스크립트 업데이트 중 오류가 발생했습니다.", data=str(e))

                return {"id": result.id, "title": result.title}
        else:
            if self.get_script_count(session, user_id) >= 5:
                raise ServerException("프로젝트는 최대 5개까지 생성할 수 있습니다.")
            shorts = Shorts(
                user_id=user_id,
                title=request.title
                or await google_ai_service.summarize_text(
                    " ".join([scene.description or "" for scene in request.shorts_json.scenes])
                ),
                shorts_json=request.shorts_json.model_dump(),
                status="ACTIVE",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            try:
                session.add(shorts)
                session.commit()
                session.refresh(shorts)
            except Exception as e:
                session.rollback()
                raise ServerException("스크립트 생성 중 오류가 발생했습니다.", data=str(e))

            return {"id": shorts.id, "title": shorts.title}

    def get_script_count(self, session: Session, user_id: int) -> int:
        statement = select(func.count(Shorts.id)).where(Shorts.user_id == user_id, Shorts.status != "DELETED")
        result = session.exec(statement).first()
        print(result)
        return result or 0

    def batch_delete_scripts(self, session: Session, user_id: int, script_ids: list[int]) -> bool:
        if not script_ids:
            return True

        statement = select(Shorts).where(Shorts.id.in_(script_ids), Shorts.user_id == user_id)
        results = session.exec(statement).all()

        if not results:
            return False

        try:
            for result in results:
                result.status = "DELETED"
                session.add(result)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise ServerException("스크립트 일괄 삭제 중 오류가 발생했습니다.", data=str(e))
