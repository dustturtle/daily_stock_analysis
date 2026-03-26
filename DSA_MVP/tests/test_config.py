# -*- coding: utf-8 -*-
"""Tests for DSA_MVP.config"""

from DSA_MVP.config import load_config


class TestConfig:
    """Config 加载测试"""

    def test_default_config(self, monkeypatch):
        """未设置环境变量时应返回默认值"""
        monkeypatch.delenv("STOCK_LIST", raising=False)
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        monkeypatch.delenv("LLM_BASE_URL", raising=False)
        monkeypatch.delenv("LLM_MODEL", raising=False)
        monkeypatch.delenv("DB_PATH", raising=False)

        cfg = load_config(env_path="/dev/null")
        assert cfg.stock_list == []
        assert cfg.llm_api_key == ""
        assert cfg.llm_base_url == "https://api.deepseek.com"
        assert cfg.llm_model == "deepseek-chat"
        assert cfg.db_path == "data/analysis.db"

    def test_load_from_env(self, monkeypatch):
        """从环境变量加载配置"""
        monkeypatch.setenv("STOCK_LIST", "600519,300750,000001")
        monkeypatch.setenv("LLM_API_KEY", "sk-test-key")
        monkeypatch.setenv("LLM_BASE_URL", "https://api.example.com")
        monkeypatch.setenv("LLM_MODEL", "gpt-4o")
        monkeypatch.setenv("DB_PATH", "/tmp/test.db")

        cfg = load_config(env_path="/dev/null")
        assert cfg.stock_list == ["600519", "300750", "000001"]
        assert cfg.llm_api_key == "sk-test-key"
        assert cfg.llm_base_url == "https://api.example.com"
        assert cfg.llm_model == "gpt-4o"
        assert cfg.db_path == "/tmp/test.db"

    def test_load_from_env_file(self, tmp_path):
        """从 .env 文件加载配置"""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "STOCK_LIST=600519\n"
            "LLM_API_KEY=sk-file-key\n"
            "LLM_MODEL=deepseek-chat\n"
        )
        cfg = load_config(env_path=str(env_file))
        assert cfg.stock_list == ["600519"]
        assert cfg.llm_api_key == "sk-file-key"

    def test_empty_stock_list(self, monkeypatch):
        """空 STOCK_LIST 应返回空列表"""
        monkeypatch.setenv("STOCK_LIST", "")
        cfg = load_config(env_path="/dev/null")
        assert cfg.stock_list == []

    def test_stock_list_whitespace_handling(self, monkeypatch):
        """STOCK_LIST 中的空格应被自动去除"""
        monkeypatch.setenv("STOCK_LIST", " 600519 , 300750 , ")
        cfg = load_config(env_path="/dev/null")
        assert cfg.stock_list == ["600519", "300750"]
