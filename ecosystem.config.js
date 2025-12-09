module.exports = {
  apps: [
    {
      name: 'buffotte-api',
      script: 'api.py',
      interpreter: './.venv/bin/python',
      cwd: '/root/Buffotte',
      env: {
        NODE_ENV: 'production'
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      error_file: '/root/Buffotte/logs/api-error.log',
      out_file: '/root/Buffotte/logs/api-out.log',
      log_file: '/root/Buffotte/logs/api.log',
      time: true
    },
    {
      name: 'buffotte-frontend',
      script: 'npm',
      args: 'run preview',
      cwd: '/root/Buffotte/frontend',
      env: {
        NODE_ENV: 'production',
        PORT: 4173
      },
      instances: 1,
      exec_mode: 'fork_mode',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: '/root/Buffotte/logs/frontend-error.log',
      out_file: '/root/Buffotte/logs/frontend-out.log',
      log_file: '/root/Buffotte/logs/frontend.log',
      time: true
    }
  ]
};