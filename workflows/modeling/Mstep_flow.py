###### Mstep_flow.py ######
#!/usr/bin/env python
"""
Pipeline description documentation.

AStepFlow Arguments:

	Required Arguments:
		-i, --input_config 
"""
import argparse
import sys
import os
import time
import json

from subprocess import call
from pyflow import WorkflowRunner
from workflows.utils.args import add_pyflow_args
from workflows.utils.args import default_pyflow_args
from workflows.utils.args import extend_pyflow_docstring

#from workflows.utils.sys_utils import ensure_file_exists
#from workflows.config import SiteConfig

__version__ = "0.0.1"

class MStepFlow(WorkflowRunner):
	def __init__(self, input_config):#, input, output_dir, nstruct, freq, last_freq, actDist=None):
		self.input_config = input_config
		# self.sys_config = sys_config
		# self.input = input
		# self.output_dir = output_dir
		# self.nstruct = int(nstruct)
		# self.freq = freq
		# self.last_freq = last_freq
		
		# self.actDist = actDist
				
# input validation
		#ensure_file_exists(self.bam)

	def workflow(self):
		if type(self.input_config) == str :
			if not (os.path.exists(self.input_config) and os.access(self.input_config, os.R_OK) ):
				raise Exception('Cannot Find or Access input_config file %s' % self.input_config)
			with open(self.input_config, 'r') as data_file: 
				self.input_config = json.load(data_file)
		
		if not self.input_config.has_key('source_dir') :
			raise Exception('Input config error, it does not have source_dir ')		
					
		if not self.input_config.has_key('modeling_parameters') :
			raise Exception('%s : Input config error, it does not have modeling_parameters' % os.path.name(__file__))
		else :
			if not self.input_config['modeling_parameters'].has_key('probMat') :
				raise Exception('%s : Input config error, it does not have probMat' % os.path.name(__file__))
			if not self.input_config['modeling_parameters'].has_key('last_freq') :
				raise Exception('%s : Input config error, it does not have last_freq' % os.path.name(__file__))
			if not self.input_config['modeling_parameters'].has_key('freq') :
				raise Exception('%s : Input config error, it does not have freq' % os.path.name(__file__))
			if not self.input_config['modeling_parameters'].has_key('num_of_structures') :
				raise Exception('%s : Input config error, it does not have num_of_structures' % os.path.name(__file__))
			
		mstep_src = '%s/Mstep.py' % self.input_config['source_dir']
		nstruct = self.input_config['modeling_parameters']['num_of_structures']
	
		task_list = ["%s%d" % ("copy", i) for i in range(nstruct)]
		priority_list = [int(i/100) for i in range(nstruct)]
		
		for task, priority in zip(task_list, priority_list):
			task_config = self.input_config
			task_config['modeling_parameters'].update({'output_file' : '%s/%s.hms' % (task_config['modeling_parameters']['struct_dir'], task)})
			
			# args = [
				# 'python',
				# mstep_src, 
				# '--probfile', self.input,
				# '--lastfb', self.last_freq,
				# '--currentfb', self.freq,
				# '--output_file', '%s/%s.hms' % (self.output_dir, task)
			# ]
			
			args = [
				'python', 
				mstep_src, 
				'--input_config', json.dumps(task_config)
				]
				
			#if self.actDist != None :
			#	args.extend(['--actdistfile', self.actDist])

		# if self.flag:
			# args.append('--flag')

			self.addTask(label=task, command=' '.join(args), nCores=1, memMb=1500, retryMax=3, retryWait=2, retryWindow=0, retryMode='all')
			time.sleep(0.2)
			
if __name__ == "__main__":
	parser = argparse.ArgumentParser(usage=extend_pyflow_docstring(__doc__))
	parser.add_argument('-i', '--input_config', type=str, required=True)
	# parser.add_argument('-c', '--sys_config', type=str, required=True)
	# parser.add_argument('-i', '--input', type=str, required=True)
	# parser.add_argument('-o', '--output_dir', type=str, required=True)
	# parser.add_argument('-n', '--nstruct', type=str, required=True)
	# parser.add_argument('-f', '--freq', type=str, required=True)
	# parser.add_argument('-l', '--last_freq', type=str, required=True)
	# parser.add_argument('-a', '--actDist', type=str, required=False)
	# parser.add_argument('--flag', default=False, action="store_true")
	add_pyflow_args(parser)
	args = parser.parse_args()

	# mstep_wf = MStepFlow(
			# args.sys_config,
			# args.input,
			# args.output_dir,
			# args.nstruct,
			# args.freq,
			# args.last_freq,
			# args.actDist
			# )
	mstep_wf = MStepFlow(args.input_config)

	sys.exit(mstep_wf.run(**default_pyflow_args(args)))