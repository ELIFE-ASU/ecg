import csv
import Bio
import os
import Bio.TogoWS as TogoWS
# import cPickle as pickle

def txt_to_list(filename):
    return [x[0] for x in csv.reader(open(filename,'r'),delimiter='\t')]

## Test
def test_txt_to_list():
    assert len(txt_to_list("newdata/20171129/compound.txt")) == 18132
    assert len(txt_to_list("newdata/20171129/enzyme.txt")) == 7111
    assert len(txt_to_list("newdata/20171129/reaction.txt")) == 10664

def write_kegg_entries(filename,dirname,entry_type):
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    if entry_type == "compound":
        stripstring = "cpd:"
    elif entry_type == "enzyme":
        stripstring = "ec:"
    elif entry_type == "reaction":
        stripstring = "rn:"

    entries = txt_to_list(filename)

    for i,entry in enumerate(entries):
        
        entry_id = entry.strip(stripstring)
        entry_fname = entry_id+".json"

        print "Saving (verifying) %s entry %s of %s (%s)..."%(entry_type,i+1,len(entries),entry_id)

        while entry_fname not in os.listdir(dirname):
            try:
                handle = TogoWS.entry(entry_type, entry_id, format="json")
                with open(dirname+'/'+entry_fname, 'a') as f:
                    f.write(handle.read())
            except:
                pass

def main():
    test_txt_to_list()

    # filename = "newdata/20171201/compound.txt"
    # dirname = "newdata/20171201/compounds"
    # entry_type = "compound"
    # write_kegg_entries(filename,dirname,entry_type)

    # filename = "newdata/20171201/enzyme.txt"
    # dirname = "newdata/20171201/enzymes"
    # entry_type = "enzyme"
    # write_kegg_entries(filename,dirname,entry_type)

    filename = "newdata/20171201/reaction.txt"
    dirname = "newdata/20171201/reactions"
    entry_type = "reaction"
    write_kegg_entries(filename,dirname,entry_type)

if __name__ == '__main__':
    main()


