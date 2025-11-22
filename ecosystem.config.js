module.exports = {
  apps: [{
    name: 'buffotte-api',
    script: 'run_api.py',
    interpreter: 'python3',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    }
  }]
};