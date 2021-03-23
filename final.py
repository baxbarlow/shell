#Bax, Eddie, Austin Shell Project
import os
import shlex
import sys
import signal
import subprocess

class Job:
	def __init__(self, process, job_num, pid, command):
		self.process = process
		self.job_num = job_num
		self.pid = pid
		self.command = command

	def __repr__(self):
		return (str(self.job_num) + "	" + str(self.pid) + ": " + str(self.command))

def output_redirect(line, location):     
	command_initial = []      
	stdout = ""  
	file_redirect = ""
	carrot_point = 0
	split = line.split()
	for i in range(len(split)):
		if line.split()[i] == ">":
			carrot_point = i
			file_redirect = line.split()[i+1]

	for j in range(carrot_point - 1, 0, -1):
		if "-" not in line.split()[carrot_point - 1]:
			command_initial.append(line.split()[carrot_point-1])
			break	
		else: 
			while "-" in line.split()[j]:
				command_initial.append(line.split()[j])
			command_initial.append(line.split()[carrot_point-1])
	result = subprocess.run(command_initial, stdout = subprocess.PIPE)
	print("file_redirect")
	with open(file_redirect, 'w') as f:
		f.write(result.stdout)

def command_pipe(line, location):
	#duplicates the stdin and stdout
	stdin = os.dup(0)
	stdout = os.dup(1)
	pipe_in = os.dup(stdin)
	#splits the command into induvidual commands and goes through each one
	for command in line.split("|"):
		os.dup2(pipe_in, 0)
		os.close(pipe_in)
		#if it's the last command, get the output ready
		if command == line.split("|")[-1]:
			pipe_out = os.dup(stdout)
		else:
			pipe_in, pipe_out = os.pipe()
		#pipe stdout
		os.dup2(pipe_out, 1)
		os.close(pipe_out)
		subprocess.run(command.strip().split())
	#close and restor stdin and stdout
	os.dup2(stdin, 0)
	os.dup2(stdout, 1)
	os.close(stdin)
	os.close(stdout)


def sh_loop():
	home_dir = os.getcwd()
	jobs = []
	job_num = 0
	foreground = None
	while True:
		#gets location and asks for input
		location = os.getcwd()
		stdin = input("[" + location + "]"+ " $ ")
		try:
			if len(stdin.strip()) == 0:
				continue
			if "|" in stdin:
				command_pipe(stdin, location)
			else:
				#splits the input into arguments
				args = shlex.split(stdin)
				#if the input has any of the special operators, use os.system
				if "*" in stdin or "$(" in stdin or ">" in stdin or "<" in stdin:
					os.system(stdin)
				else:
					if stdin == "exit":
						print("Exiting shell...")
						sys.exit()
					elif "cd" == args[0]:
						if stdin.strip() == "cd":
							os.chdir(home_dir)
						else:
							try:
								os.chdir(location + "/" +  args[1])
							except:
								print(args[1] + " is not a valid directory")
					elif stdin.strip() == "pwd":
						print(os.getcwd())
					#goes through every job and prints
					elif stdin.strip() == "jobs":
						for job in jobs:
							print(job)
					elif "bg" == args[0]:
						if len(args) == 1:
							print("Moves a process to the background")
						else:
							pid = args[1]
							jobFound = False
							for job in jobs:
								if job.pid == pid:
									jobFound = True
							#once the job is found, stops signal and moves it to the background
							if jobFound:
								for job in jobs:
									if job.pid == pid:
										os.kill(job.pid, signal.SIGSTOP)
										os.kill(job.pid, signal.SIGCONT)
							else:
								print("Job not found")
					elif "fg" == args[0]:
						if len(args) == 1:
							print("Moves a process to the foreground")
						else:
							pid = args[1]
							jobFound = False
							for job in jobs:
								if job.pid == pid:
									jobFound = True
							#once the job is found, stops the process and move it to the foreground
							if jobFound:
								for job in jobs:
									if job.job_num == pid:
										os.kill(job.pid, signal.SIGSTOP)
										foreground = pid
										job.process.wait()
							else:
								print("Job not found")
								
					else:
						try:
							#opens a subprocess with Popen
							process = subprocess.Popen(args)
							#adds the job to the job list
							jobs.append(Job(process, job_num, process.pid, stdin))
							job_num += 1
							#sets the foreground to the current process and waits for it to complete
							foreground = process.pid
							process.wait()
							foreground = None
						except:
							print("Command not found")
		#every iteration, it clears jobs that have completed from the list
		except KeyboardInterrupt:
			if foreground == None:
				print("foreground empty")
			else:
				os.kill(foreground, signal.SIGINT)
		for job in jobs:
			if job != None and job.process.poll() is not None:
				jobs.remove(job)
		#in the case of keyboard interruption, then it sends a SIGNINT signal to the foreground
		
def main():
	sh_loop()

if __name__ == "__main__":
	main()