from datetime import datetime, timedelta

from monitor import DomainExpirationMonitor


def test_add_and_remove_domain(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    m = DomainExpirationMonitor()
    monkeypatch.setattr(m, 'get_expiration_date', lambda _: datetime.now() + timedelta(days=40))
    m.add_domain('example.com')
    assert 'example.com' in m.domains['domains']
    m.remove_domain('example.com')
    assert 'example.com' not in m.domains['domains']
