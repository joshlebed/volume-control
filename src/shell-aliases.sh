alias vc-help="cat ${PATH_TO_VOLUME_CONTROL_REPO}/README.md"
alias vc-start="nohup ${PATH_TO_VOLUME_CONTROL_REPO}/.venv/bin/python ${PATH_TO_VOLUME_CONTROL_REPO}/src/volume_control.py &> /tmp/nohup.out & disown"
alias vc-start-foreground="${PATH_TO_VOLUME_CONTROL_REPO}/.venv/bin/python ${PATH_TO_VOLUME_CONTROL_REPO}/src/volume_control.py"
alias vc-tail-logs="tail -f /tmp/volume_controller.log"
alias vc-list="ps aux | grep volume_control | grep -v grep | grep -v tail"
alias vc-kill="vc-list | awk '{print \$2}' | xargs kill"
alias vc-kill-better='pkill -f ".*volume_controller.*"' # ask julian for the rest
alias vc-restart="vc-kill; vc-start"
