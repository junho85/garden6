"""
Slack Markdown 처리를 위한 간단한 유틸리티
python-markdown-slack 패키지 대체용
"""

import re
import markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor


class SlackMarkdownPreprocessor(Preprocessor):
    """Slack 특수 문법을 일반 마크다운으로 변환"""
    
    def run(self, lines):
        text = '\n'.join(lines)
        
        # Slack 사용자 멘션 처리: <@U12345> -> @user
        text = re.sub(r'<@([UW][A-Z0-9]+)>', r'@\1', text)
        
        # Slack 채널 멘션 처리: <#C12345|channel> -> #channel
        text = re.sub(r'<#([C][A-Z0-9]+)\|([^>]+)>', r'#\2', text)
        
        # Slack URL 처리: <http://example.com|text> -> [text](http://example.com)
        text = re.sub(r'<(https?://[^|>]+)\|([^>]+)>', r'[\2](\1)', text)
        
        # 간단한 URL 처리: <http://example.com> -> [http://example.com](http://example.com)
        text = re.sub(r'<(https?://[^>]+)>', r'[\1](\1)', text)
        
        # Slack 특수 문자 이스케이프 해제
        text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        
        return text.split('\n')


class SlackMarkdownExtension(Extension):
    """Slack Markdown 확장"""
    
    def extendMarkdown(self, md):
        md.preprocessors.register(
            SlackMarkdownPreprocessor(md),
            'slack_markdown',
            175
        )


def slack_markdown_to_html(text):
    """Slack 마크다운 텍스트를 HTML로 변환"""
    if not text:
        return text
    
    md = markdown.Markdown(extensions=[SlackMarkdownExtension()])
    return md.convert(text)