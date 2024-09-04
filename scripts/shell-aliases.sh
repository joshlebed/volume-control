alias volume-control-help='cat /home/pi/code/volume-control/README.md'
alias volume-control-start='nohup python3.11 ~/code/volume-control/scripts/volume_controller_evdev_lirc.py &> /tmp/nohup.out & disown'
alias volume-control-start-foreground='python3.11 ~/code/volume-control/scripts/volume_controller_evdev_lirc.py'
alias volume-control-tail-logs='tail -f /tmp/volume_controller.log'
alias volume-control-list='ps aux | grep volume_controller_evdev_lirc | grep -v grep'
alias volume-control-kill="volume-control-list | awk '{print \$2}' | xargs kill"
alias volume-control-kill-better='pkill -f ".*volume_controller.*"' # ask julian for the rest
alias volume-control-restart="volume-control-kill; volume-control-start"
