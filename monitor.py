#!/usr/bin/env python3
"""
Domain Expiration Monitor
Monitor multiple domains and get alerts before expiration
"""

import os
import sys
import argparse
import json
import socket
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from dotenv import load_dotenv
try:
    import schedule
except ImportError:
    schedule = None

try:
    import whois
    WHOIS_AVAILABLE = True
except ImportError:
    WHOIS_AVAILABLE = False
    print("⚠️  python-whois not installed. Install with: pip install python-whois")

load_dotenv()

class DomainExpirationMonitor:
    def __init__(self):
        self.domains_file = 'domains.json'
        self.domains = self.load_domains()
        
        # Alert settings
        alert_days_str = os.getenv('ALERT_DAYS_BEFORE', '30,14,7,1')
        self.alert_days = [int(d) for d in alert_days_str.split(',')]
        
        # Notification settings
        self.email_to = os.getenv('EMAIL_TO')
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
    
    def load_domains(self) -> Dict:
        """Load monitored domains from file"""
        if os.path.exists(self.domains_file):
            with open(self.domains_file, 'r') as f:
                return json.load(f)
        return {'domains': {}}
    
    def save_domains(self):
        """Save monitored domains to file"""
        with open(self.domains_file, 'w') as f:
            json.dump(self.domains, f, indent=2)
    
    def add_domain(self, domain: str):
        """Add domain to monitoring"""
        domain = domain.lower().strip()
        
        if domain in self.domains['domains']:
            print(f"⚠️  Domain {domain} already monitored")
            return
        
        # Get initial expiration date
        expiration = self.get_expiration_date(domain)
        
        self.domains['domains'][domain] = {
            'added': datetime.now().isoformat(),
            'expiration': expiration.isoformat() if expiration else None,
            'last_checked': datetime.now().isoformat(),
            'alerts_sent': []
        }
        
        self.save_domains()
        print(f"✅ Added domain: {domain}")
        if expiration:
            print(f"   Expiration: {expiration.strftime('%Y-%m-%d')}")
    
    def remove_domain(self, domain: str):
        """Remove domain from monitoring"""
        domain = domain.lower().strip()
        
        if domain in self.domains['domains']:
            del self.domains['domains'][domain]
            self.save_domains()
            print(f"✅ Removed domain: {domain}")
        else:
            print(f"❌ Domain {domain} not found")
    
    def get_expiration_date(self, domain: str) -> Optional[datetime]:
        """Get domain expiration date using WHOIS"""
        if not WHOIS_AVAILABLE:
            print("⚠️  python-whois not available")
            return None
        
        try:
            w = whois.whois(domain)
            
            # Try different expiration date fields
            expiration = None
            if hasattr(w, 'expiration_date'):
                if isinstance(w.expiration_date, list):
                    expiration = w.expiration_date[0]
                else:
                    expiration = w.expiration_date
            
            if expiration and isinstance(expiration, datetime):
                return expiration
            
            return None
        except Exception as e:
            print(f"❌ Error checking {domain}: {e}")
            return None
    
    def check_domain(self, domain: str) -> Dict:
        """Check domain expiration status"""
        domain_data = self.domains['domains'].get(domain)
        if not domain_data:
            return None
        
        # Update expiration date
        expiration = self.get_expiration_date(domain)
        if expiration:
            domain_data['expiration'] = expiration.isoformat()
        
        domain_data['last_checked'] = datetime.now().isoformat()
        
        if not expiration:
            return {
                'domain': domain,
                'status': 'unknown',
                'expiration': None,
                'days_until_expiration': None
            }
        
        now = datetime.now()
        days_until = (expiration - now).days
        
        # Determine status
        if days_until < 0:
            status = 'expired'
        elif days_until < 7:
            status = 'critical'
        elif days_until < 30:
            status = 'warning'
        else:
            status = 'ok'
        
        return {
            'domain': domain,
            'status': status,
            'expiration': expiration,
            'days_until_expiration': days_until
        }
    
    def send_slack_alert(self, domain: str, days_until: int, expiration: datetime):
        """Send Slack alert"""
        if not self.slack_webhook:
            return
        
        try:
            color = {
                'expired': '#FF0000',
                'critical': '#FF6B00',
                'warning': '#FFA500',
                'ok': '#36A64F'
            }.get('expired' if days_until < 0 else 'critical' if days_until < 7 else 'warning' if days_until < 30 else 'ok', '#808080')
            
            message = {
                "text": f"Domain Expiration Alert: {domain}",
                "attachments": [
                    {
                        "color": color,
                        "title": f"Domain: {domain}",
                        "fields": [
                            {
                                "title": "Days Until Expiration",
                                "value": f"{days_until} days" if days_until >= 0 else "EXPIRED",
                                "short": True
                            },
                            {
                                "title": "Expiration Date",
                                "value": expiration.strftime('%Y-%m-%d'),
                                "short": True
                            }
                        ],
                        "footer": "Domain Expiration Monitor"
                    }
                ]
            }
            
            requests.post(self.slack_webhook, json=message)
        except Exception as e:
            print(f"❌ Slack alert error: {e}")
    
    def check_all_domains(self):
        """Check all monitored domains"""
        if not self.domains['domains']:
            print("No domains to monitor. Add domains with --add")
            return
        
        print(f"🔍 Checking {len(self.domains['domains'])} domain(s)...")
        
        for domain in list(self.domains['domains'].keys()):
            result = self.check_domain(domain)
            
            if not result:
                continue
            
            days_until = result['days_until_expiration']
            expiration = result['expiration']
            
            if days_until is None:
                print(f"⚠️  {domain}: Could not determine expiration date")
                continue
            
            # Check if alert should be sent
            domain_data = self.domains['domains'][domain]
            alerts_sent = domain_data.get('alerts_sent', [])
            
            for alert_days in self.alert_days:
                if days_until <= alert_days and days_until > 0:
                    alert_key = f"{alert_days}_days"
                    if alert_key not in alerts_sent:
                        print(f"🔔 Alert: {domain} expires in {days_until} days ({expiration.strftime('%Y-%m-%d')})")
                        self.send_slack_alert(domain, days_until, expiration)
                        alerts_sent.append(alert_key)
                        domain_data['alerts_sent'] = alerts_sent
                        break
            
            if days_until < 0:
                print(f"🚨 {domain}: EXPIRED!")
            elif days_until < 7:
                print(f"⚠️  {domain}: {days_until} days until expiration (CRITICAL)")
            elif days_until < 30:
                print(f"⚠️  {domain}: {days_until} days until expiration")
            else:
                print(f"✓ {domain}: {days_until} days until expiration")
        
        self.save_domains()
    
    def list_domains(self):
        """List all monitored domains"""
        if not self.domains['domains']:
            print("No domains monitored")
            return
        
        print("\n" + "="*80)
        print("MONITORED DOMAINS")
        print("="*80)
        
        for domain, data in self.domains['domains'].items():
            expiration_str = "Unknown"
            days_str = "N/A"
            
            if data.get('expiration'):
                expiration = datetime.fromisoformat(data['expiration'])
                now = datetime.now()
                days_until = (expiration - now).days
                expiration_str = expiration.strftime('%Y-%m-%d')
                days_str = f"{days_until} days"
            
            print(f"\n{domain}")
            print(f"  Expiration: {expiration_str}")
            print(f"  Days Until: {days_str}")
            print(f"  Last Checked: {data.get('last_checked', 'Never')}")
    
    def run_continuous(self, interval: int = 86400):
        """Run continuous monitoring"""
        if schedule is None:
            raise RuntimeError("schedule package is required for continuous mode")
        print(f"🚀 Starting continuous domain monitoring (checking every {interval}s)")
        
        schedule.every(interval).seconds.do(self.check_all_domains)
        
        # Initial check
        self.check_all_domains()
        
        while True:
            schedule.run_pending()
            time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description='Domain Expiration Monitor')
    parser.add_argument('--add', help='Add domain to monitor')
    parser.add_argument('--remove', help='Remove domain from monitoring')
    parser.add_argument('--list', action='store_true', help='List monitored domains')
    parser.add_argument('--check', action='store_true', help='Check all domains')
    parser.add_argument('--watch', action='store_true', help='Run continuous monitoring')
    parser.add_argument('--interval', type=int, default=86400, help='Check interval in seconds (default: 86400 = 24h)')
    
    args = parser.parse_args()
    
    try:
        monitor = DomainExpirationMonitor()
        
        if args.add:
            monitor.add_domain(args.add)
        elif args.remove:
            monitor.remove_domain(args.remove)
        elif args.list:
            monitor.list_domains()
        elif args.check:
            monitor.check_all_domains()
        elif args.watch:
            monitor.run_continuous(args.interval)
        else:
            parser.print_help()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

