import urllib.robotparser
from loguru import logger

class RobotsChecker:
    """
    遵循 robots.txt 禮儀檢查器
    確認目標路徑是否被禁止抓取
    """
    def __init__(self, user_agent: str = "PriceBot/1.0 (+https://cursor-class.internal)"):
        self.user_agent = user_agent
        self.parser = urllib.robotparser.RobotFileParser()

    def load_from_text(self, robots_txt_content: str):
        self.parser.parse(robots_txt_content.splitlines())

    def can_fetch(self, url: str) -> bool:
        allowed = self.parser.can_fetch(self.user_agent, url)
        if not allowed:
            logger.warning(f"🚫 [合規阻擋] 依據 robots.txt 規範，拒絕爬取：{url}")
        else:
            logger.info(f"✅ [合規通過] robots.txt 允許爬取：{url}")
        return allowed
