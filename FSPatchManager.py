# File System Patch Manager, for managing applications
# and removals of modular file overwrites of an application's
# resources, when they are represented by a file tree
# Copyright notice for this file:
#  Copyright (C) 2021 Hextator

# Tested with Python 3.2

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see
# https://www.gnu.org/licenses/gpl-3.0.en.html

import sys

import os
import shutil

import hashlib

# Copied from Hexware.IOExt, available from the same author
def ensureDir(path):
	if os.path.isdir(path):
		return
	try:
		os.makedirs(path)
	except OSError as ose:
		try:
			if ose.errno != errno.EEXIST:
				raise
		except NameError: pass
	except Exception as e:
		try:
			if type(e) is WindowsError:
				if 17 != e.errno:
					raise
		except: pass

def ensureDirectory(dirPath):
	ensureDir(dirPath)

def copyFile(sourcePath, targetPath):
	if os.path.exists(targetPath):
		raise OSError(targetPath + ' already exists')
	ensureDirectory(os.path.dirname(targetPath))
	shutil.copyfile(sourcePath, targetPath)

def copyFileSilentFail(sourcePath, targetPath):
	try:
		copyFile(sourcePath, targetPath)
	except: pass

def overwriteFile(sourcePath, targetPath):
	ensureDirectory(os.path.dirname(targetPath))
	shutil.copyfile(sourcePath, targetPath)

def overwriteFileSilentFail(sourcePath, targetPath):
	try:
		overwriteFile(sourcePath, targetPath)
	except: pass

def deleteFile(filePath):
	os.remove(filePath)

def deleteFileSilentFail(filePath):
	try:
		deleteFile(filePath)
	except: pass

def deleteDirectory(dirPath):
	if os.path.isdir(dirPath):
		shutil.rmtree(dirPath)

def getHash(filePath):
	data = None
	with open(filePath, 'rb') as fileHandle:
		data = fileHandle.read()
	md5 = hashlib.md5()
	md5.update(data)
	return md5.digest()

def fileStats(filePath):
	fileSize = os.path.getsize(filePath)
	md5Hash = getHash(filePath)
	return (fileSize, md5Hash)

APP_DATA_DIR    = ''
LOG_PATH        = ''
PATCH_PATH      = ''
REVERT_PATH     = ''
GEN_PATCH_PATH  = ''
GEN_REVERT_PATH = ''

def loadSettings(settingsPath):
	global APP_DATA_DIR
	global LOG_PATH
	global PATCH_PATH
	global REVERT_PATH
	global GEN_PATCH_PATH
	global GEN_REVERT_PATH
	try:
		with open(settingsPath, 'r') as settings:
			for line in settings:
				split = line.split('=', 1)
				var = split[0].strip()
				val = split[1].strip()
				if 'APP_DATA_DIR' == var:
					APP_DATA_DIR = val
				elif 'LOG_PATH' == var:
					LOG_PATH = val
				elif 'PATCH_PATH' == var:
					PATCH_PATH = val
				elif 'REVERT_PATH' == var:
					REVERT_PATH = val
				elif 'GEN_PATCH_PATH' == var:
					GEN_PATCH_PATH = val
				elif 'GEN_REVERT_PATH' == var:
					GEN_REVERT_PATH = val
	except: pass

def ensurePatchManagerDirs():
	global APP_DATA_DIR
	global PATCH_PATH
	global REVERT_PATH
	global GEN_PATCH_PATH
	global GEN_REVERT_PATH
	ensureDirectory(APP_DATA_DIR)
	ensureDirectory(PATCH_PATH)
	ensureDirectory(REVERT_PATH)
	ensureDirectory(GEN_PATCH_PATH)
	ensureDirectory(GEN_REVERT_PATH)

def getPathMapHelper(rootDir):
	pathMap = {}
	for modName in os.listdir(rootDir):
		currModPath = os.path.join(rootDir, modName)
		if not os.path.isdir(currModPath):
			continue
		pathMap[modName] = list([os.path.join(root, name) for root, dirs, files in os.walk(currModPath, topdown = True) for name in files])
	return pathMap

def getPatchPaths():
	global PATCH_PATH
	return getPathMapHelper(PATCH_PATH)

def getPathsHelper(rootDir):
	return list([os.path.join(root, name) for root, dirs, files in os.walk(rootDir, topdown = True) for name in files])

def getGenPatchPaths():
	global GEN_PATCH_PATH
	return getPathsHelper(GEN_PATCH_PATH)

def getGenRevertPaths():
	global GEN_REVERT_PATH
	return getPathsHelper(GEN_REVERT_PATH)

def verifyBackups():
	global APP_DATA_DIR
	global GEN_PATCH_PATH
	global GEN_REVERT_PATH
	invalidBackupList = []
	currState = {}
	# For each file in the generated revert patch,
	# check if the associated file in the generated patch
	# matches the associated file in the app data dir;
	# if they don't, delete the associated file
	# from the generated revert patch,
	# and add the occurrence to the invalidBackupList list;
	# regardless, add the app data state to the currState dict
	# like currState[fileName] = (size, hash)
	ensureDirectory(GEN_REVERT_PATH)
	genRevertPaths = getGenRevertPaths()
	for currGenRevertPath in genRevertPaths:
		patchedFile = os.path.relpath(currGenRevertPath, start = GEN_REVERT_PATH)
		currAppDataPath = os.path.join(APP_DATA_DIR, patchedFile)
		currGenPatchPath = os.path.join(GEN_PATCH_PATH, patchedFile)
		currFileStats = fileStats(currAppDataPath)
		currState[patchedFile] = currFileStats
		if not os.path.isfile(currGenPatchPath):
			continue
		expectedStats = fileStats(currGenPatchPath)
		if expectedStats != currFileStats:
			deleteFileSilentFail(currGenRevertPath)
			invalidBackupList.append(patchedFile)
	return invalidBackupList, currState

def regeneratePatch():
	global APP_DATA_DIR
	global PATCH_PATH
	global REVERT_PATH
	global GEN_PATCH_PATH
	global GEN_REVERT_PATH
	# Empty the generated patch dir,
	# and empty the sorted revert patch dir;
	# then, for each file in the sorted patch dir,
	# copy the file to the generated patch dir,
	# then, if the associated revert file doesn't exist
	# in the generated revert patch dir,
	# copy the associated app data file
	# to there;
	# copy the file from the generated revert patch dir
	# to the appropriate sorted revert patch dir
	deleteDirectory(GEN_PATCH_PATH)
	deleteDirectory(REVERT_PATH)
	ensureDirectory(GEN_PATCH_PATH)
	ensureDirectory(REVERT_PATH)
	patchPaths = getPatchPaths()
	# Sorting is important here; this lets users have intuitive patch prioritization
	for currModName in sorted(patchPaths):
		for currSortedPatchPath in patchPaths[currModName]:
			currBasePath = os.path.relpath(currSortedPatchPath, start = os.path.join(PATCH_PATH, currModName))
			currGenPatchPath = os.path.join(GEN_PATCH_PATH, currBasePath)
			copyFileSilentFail(currSortedPatchPath, currGenPatchPath)
			currAppDataPath = os.path.join(APP_DATA_DIR, currBasePath)
			currGenRevertPath = os.path.join(GEN_REVERT_PATH, currBasePath)
			if not os.path.isfile(currGenRevertPath):
				copyFileSilentFail(currAppDataPath, currGenRevertPath)
			currSortedRevertPath = currSortedPatchPath.replace(PATCH_PATH, REVERT_PATH)
			copyFileSilentFail(currGenRevertPath, currSortedRevertPath)

def applyPatch(preExistingPatches):
	global APP_DATA_DIR
	global GEN_PATCH_PATH
	global GEN_REVERT_PATH
	# For each file in the generated patch,
	# if the associated preExistingPatches element
	# does not exist or does not match,
	# copy the generated patch file to the app data dir;
	# regardless, remove the associated element
	# from the preExistingPatches dict;
	# for each element left in the preExistingPatches dict,
	# cut the associated generated revert patch dir file
	# and paste it over the associated app data dir file
	ensureDirectory(GEN_PATCH_PATH)
	genPatchPaths = getGenPatchPaths()
	for currGenPatchPath in genPatchPaths:
		patchedFile = os.path.relpath(currGenPatchPath, start = GEN_PATCH_PATH)
		currAppDataPath = os.path.join(APP_DATA_DIR, patchedFile)
		currFileStats = fileStats(currGenPatchPath)
		expectedStats = None
		if patchedFile in preExistingPatches:
			expectedStats = preExistingPatches[patchedFile]
		if expectedStats != currFileStats:
			overwriteFileSilentFail(currGenPatchPath, currAppDataPath)
		if patchedFile in preExistingPatches:
			preExistingPatches.pop(patchedFile)
	for preExistingPatch in preExistingPatches:
		currAppDataPath = os.path.join(APP_DATA_DIR, preExistingPatch)
		currGenRevertPath = os.path.join(GEN_REVERT_PATH, preExistingPatch)
		overwriteFileSilentFail(currGenRevertPath, currAppDataPath)
		deleteFileSilentFail(currGenRevertPath)

def logInvalidBackups(invalidBackups):
	global LOG_PATH
	with open(LOG_PATH, 'w') as logFile:
		if invalidBackups:
			logFile.write('The following files were detected as being modified by something other than this tool:\n')
			for fileName in invalidBackups:
				logFile.write(fileName + '\n')

def main(args):
	global APP_DATA_DIR
	global LOG_PATH
	global PATCH_PATH
	global REVERT_PATH
	global GEN_PATCH_PATH
	global GEN_REVERT_PATH
	try:
		settingsPath = args[1]
		if not os.path.isfile(settingsPath):
			raise(IOError())
		loadSettings(settingsPath)
		if not APP_DATA_DIR:
			raise(ValueError())
		if not LOG_PATH:
			raise(ValueError())
		if not PATCH_PATH:
			raise(ValueError())
		if not REVERT_PATH:
			raise(ValueError())
		if not GEN_PATCH_PATH:
			raise(ValueError())
		if not GEN_REVERT_PATH:
			raise(ValueError())
	except Exception as e:
		print('Error parsing settings file.')
		raise(e)
	ensurePatchManagerDirs()
	invalidBackups, preExistingPatches = verifyBackups()
	logInvalidBackups(invalidBackups)
	regeneratePatch()
	applyPatch(preExistingPatches)

if __name__ == '__main__': main(sys.argv)
