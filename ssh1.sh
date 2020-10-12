#!/usr/bin/expect
set timeout 30
set ip [lindex $argv 0]
set cmd [lindex $argv 1]
spawn ssh c4dev@$ip
expect "Password:"
send "c4dev!\r"
expect ":~>" 
send "cd /home/jenkins-build/workspace/$cmd\r"
interact
