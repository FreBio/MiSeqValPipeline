import threading
import os, sys
import pdb
from smb.SMBConnection import SMBConnection
from smb.SMBHandler import SMBHandler
from smb.base import NotConnectedError, NotReadyError, SMBTimeout, SharedFile
import tempfile
import urllib.request

class MiSeqServerData():
    #SMB credentials - SECRET
    username = os.environ['SMB_USERNAME']
    password = os.environ['SMB_PASSWORD']
    #Specific server information
    myRequestIdentifier = "miseqvalpipeline"
    serverName = "SMB"
    domain = ""
    host = "smb.jbei.org"
    port = 139
    sharedFolder = "miseq"

    def __init__(self, uniqueID, mainLibraryFolder, subLibraryID, outputFolder):
        threading.Thread.__init__(self)
        self.id = uniqueID
        self.mainLibraryFolder = mainLibraryFolder
        self.subLibraryID = subLibraryID
        self.outputFolder = outputFolder
        self.metadata = ""

    def make_smb_connection(username,
                            password,
                            request_identifier,
                            server_name,
                            domain,
                            host,
                            port):
        conn = SMBConnection(username,
                                password,
                                request_identifier,
                                server_name,
                                domain=domain,
                                use_ntlm_v2 = True)
        conn.connect(host, port)
        return conn

    def run(self):
        try:
            conn = MiSeqServerData.make_smb_connection(MiSeqServerData.username,
                                            MiSeqServerData.password,
                                            MiSeqServerData.myRequestIdentifier,
                                            MiSeqServerData.serverName,
                                            MiSeqServerData.domain,
                                            MiSeqServerData.host,
                                            MiSeqServerData.port)

            #Get files names of fastq.gz files that correspond to subLibraryID (e.g. one if single, two if paired-end read)
            print("Reading fastq.gz file for "+self.subLibraryID)
            fastqFiles = []
            try:
                sharedFileObjs = conn.listPath(MiSeqServerData.sharedFolder, '/MiSeqOutput/'+self.mainLibraryFolder+'/Data/Intensities/BaseCalls')
                for a in sharedFileObjs:
                    #If fastq.gz file...
                    if (a.filename.endswith("fastq.gz")):
                    #And correct sample ID
                        if (a.filename.startswith(self.subLibraryID) or a.filename.startswith(self.subLibraryID.replace("_", "-"))): #For some reason, MiSeq sampleSheet.csv will escape hyphens
                            fastqFiles.append(a.filename)
                            #Now fetch and write fastq.gz files to local machine
                            director = urllib.request.build_opener(SMBHandler)
                            fh = director.open('smb://'+MiSeqServerData.username+':'+MiSeqServerData.password+'@smb.jbei.org/miseq/MiSeqOutput/'+self.mainLibraryFolder+'/Data/Intensities/BaseCalls/'+a.filename).read()
                            f = open(self.outputFolder+"/"+a.filename, 'wb')
                            f.write(fh)
                            f.close()
            except SMBTimeout:
                print("SMB server timed out")
                sys.exit(1)
            except NotReadyError:
                print("Authentication with SMB server failed")
                sys.exit(1)
            except NotConnectedError:
                print("Disconnected from SMB server")
                sys.exit(1)
            except Exception as ex:
                print("Error retrieving fastq.gz files "+str(ex))
                sys.exit(1)

            print("Writing metadata for "+self.subLibraryID)
            for filename in fastqFiles:
                #Get metadata for project's pre.libraries.info file
                proposalID = self.subLibraryID
                libraryName = "libName"
                genus = "genus"
                species = "species"
                strain = "strain"
                metaData = [proposalID, libraryName, self.outputFolder+"/"+filename, genus, species, strain]
                #Save metadata to be later printed to libraries.info file
                self.metadata += ("\t").join(metaData)+"\n";
        except SMBTimeout:
            print("SMB server timed out")
            sys.exit(1)
        except NotReadyError:
            print("Authentication with SMB server failed")
            sys.exit(1)
        except NotConnectedError:
            print("Disconnected from SMB server")
            sys.exit(1)
        except Exception as ex:
            print("Error retrieving libraries from SMB server "+str(ex))
            sys.exit(1)


class ICEServerData(threading.Thread): 
    #ICE credentials - SECRET

    def __init__(self, uniqueID, inputfile):
        threading.Thread.__init__(self)
        self.id = uniqueID
        self.inputfile = inputfile
        self.sequence = ""

    def run(self):
        try:
            #print("Reading data from ICE for "+self.inputfile)
            #f = open("../ICErefs/"+self.inputfile, "r")
            f = open("/src/test3.fasta", "r")
            #Save metadata to be later printed to references.FASTA file
            self.sequence = f.read()
        except:
            return

