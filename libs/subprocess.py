import sys
import platform
import asyncio


# Run command in subprocess
async def run_command(*args):
	# Create subprocess
	process = await asyncio.create_subprocess_exec( *args, stdout=asyncio.subprocess.PIPE )

	# Status
	print( 'Started:', args, '(pid = ' + str( process.pid ) + ')' )

	# Wait for the subprocess to finish
	stdout, stderr = await process.communicate()

	# Progress
	if process.returncode == 0:
		print( 'Done:', args, '(pid = ' + str( process.pid ) + ')' )
	else:
		print( 'Failed:', args, '(pid = ' + str( process.pid ) + ')' )

	# Result
	result = stdout.decode().strip()

	# Return stdout
	return result


# Run command in subprocess (shell), This can be used if you wish to execute e.g. "copy" on Windows, which can only be executed in the shell.
async def run_command_shell(command):
	# Create subprocess
	process = await asyncio.create_subprocess_shell(
			command,
			stdout=asyncio.subprocess.PIPE )

	# Status
	print( 'Started:', command, '(pid = ' + str( process.pid ) + ')' )

	# Wait for the subprocess to finish
	stdout, stderr = await process.communicate()

	# Progress
	if process.returncode == 0:
		print( 'Done:', command, '(pid = ' + str( process.pid ) + ')' )
	else:
		print( 'Failed:', command, '(pid = ' + str( process.pid ) + ')' )

	# Result
	result = stdout.decode().strip()

	# Return stdout
	return result


# Yield successive n-sized chunks from l.
def make_chunks(l, n):
	if sys.version_info.major == 2:
		for i in range( 0, len( l ), n ):
			yield l[i:i + n]
	else:
		# Assume Python 3
		for i in range( 0, len( l ), n ):
			yield l[i:i + n]


# Run tasks asynchronously using asyncio and return results
# If max_concurrent_tasks are set to 0, no limit is applied.
# By default, Windows uses SelectorEventLoop, which does not support subprocesses. Therefore ProactorEventLoop is used on Windows.
def run_asyncio_commands(tasks, max_concurrent_tasks=0):

	all_results = []

	if max_concurrent_tasks == 0:
		chunks = [tasks]
	else:
		chunks = make_chunks( l=tasks, n=max_concurrent_tasks )

	for tasks_in_chunk in chunks:
		if platform.system() == 'Windows':
			loop = asyncio.ProactorEventLoop()
			asyncio.set_event_loop( loop )
		else:
			loop = asyncio.get_event_loop()

		commands = asyncio.gather( *tasks_in_chunk )  # Unpack list using *
		results = loop.run_until_complete( commands )
		all_results += results
		loop.close()
	return all_results