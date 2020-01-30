import unittest
import os
import ecg

## Test kegg.update release change
## - if current release ("test") doesn't match retrieved release, update and 
##   check to make sure keys in the version.json and master.json match what 
##   they should be
## - test second update to verify it works the same way

# class TestKeggUpdateReleaseChange(unittest.TestCase):

## Test kegg.update list change
## - if retrieved lists added key compared to the current lists, check to make sure
##   new written version.json has added key in the list, and write fields still match.
## - check to see if the reaction directory was updated accordingly
## - if retrieved lists removed key compared to the current lists, check to make sure
##   new written version.json has added key in the list, and write fields still match.
## - check to see if reaction directory is unmodified (it should not be modified)
## - test second update to verify it works the same way