```bash
docker compose up -d
docker logs -f realtime-localai-1 # Follow on screen model downloads
sudo bash setup.sh # sudo is required for installing host dependencies
bash run.sh
```

Note: first time you start docker compose it will take a while to download the available models

Configuration:

- This is optimized for CPU, however, you can run LocalAI with a GPU and have better performance (and run also bigger/better models).
- The python part will download torch for CPU - this is fine, it's actually not used as computation is offloaded to LocalAI
- The python part will only run silero-vad which is fast and record the audio
- The python part is meant to run by thin client such as Raspberry PIs, etc, while LocalAI can handle the bigger workload
