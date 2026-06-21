#!/bin/bash
cd /media/lz/baba/SkillOpt
source /media/lz/baba/skillopt_env/bin/activate
python -m skillopt_sleep run >> ~/.skillopt-sleep/cron.log 2>&1