"""
desiutil.maskbits
=================

Mask bits for the spectro pipeline.

Individual packages will define their own mask bits and use this as a utility
access wrapper.  Typical users will not need to construct BitMask objects on
their own.

Stephen Bailey, Lawrence Berkeley National Lab
Fall 2015

Example::

    from desiutil.maskbits import BitMask

    import yaml
    _bitdefs = yaml.load('''
    #- CCD pixel mask
    ccdmask:
        - [BAD,       0, "Pre-determined bad pixel (any reason)"]
        - [HOT,       1, "Hot pixel"]
        - [DEAD,      2, "Dead pixel"]
        - [SATURATED, 3, "Saturated pixel from object"]
        - [COSMIC,    4, "Cosmic ray"]
    ''')
    ccdmask = BitMask('ccdmask', _bitdefs)

    ccdmask.COSMIC | ccdmask.SATURATED
    ccdmask.mask('COSMIC')     #- 2**4, same as ccdmask.COSMIC
    ccdmask.mask(4)            #- 2**4, same as ccdmask.COSMIC
    ccdmask.COSMIC             #- 2**4, same as ccdmask.mask('COSMIC')
    ccdmask.bitnum('COSMIC')   #- 4
    ccdmask.bitname(4)         #- 'COSMIC'
    ccdmask.names()            #- ['BAD', 'HOT', 'DEAD', 'SATURATED', 'COSMIC']
    ccdmask.names(3)           #- ['BAD', 'HOT']
    ccdmask.comment(0)         #- "Pre-determined bad pixel (any reason)"
    ccdmask.comment('COSMIC')  #- "Cosmic ray"    
"""

#- Move these definitions into a separate yaml file

#- Class to provide mask bit utility functions
class BitMask(object):
    """BitMask object.
    """
    def __init__(self, name, bitdefs):
        """
        Args:
            name : name of this mask, must be key in bitdefs
            bitdefs : dictionary of different mask bit definitions;
                each value is a list of [bitname, bitnum, comment]

        Typical users are not expected to create BitMask objects directly.
        """
        self._name = name
        self._bitname = dict()  #- key num -> value name
        self._bitnum = dict()   #- key name -> value num
        self._comment = dict()  #- key name or num -> comment
        self._extra = dict()
        for x in bitdefs[name]:
            bitname, bitnum, comment = x[0:3]
            assert bitname not in self._bitnum
            assert bitnum not in self._bitname
            self._bitnum[bitname] = bitnum
            self._bitname[bitnum] = bitname
            self._comment[bitname] = comment
            self._comment[bitnum] = comment
            
            if len(x) == 4:
                self._extra[bitname] = x[3]
            else:
                self._extra[bitname] = dict()

    def extra(self, bitname):
        """Return extra metadata for bitname (or an empty dict if no extra info)"""
        return self._extra[bitname]

    def bitnum(self, bitname):
        """Return bit number (int) for bitname (string)"""
        return self._bitnum[bitname]

    def bitname(self, bitnum):
        """Return bit name (string) for this bitnum (integer)"""
        return self._bitname[bitnum]

    def comment(self, bitname_or_num):
        """Return comment for this bit name or bit number"""
        return self._comment[bitname_or_num]

    def mask(self, name_or_num):
        """Return mask value, i.e. 2**bitnum for this name or number"""
        if isinstance(name_or_num, int):
            return 2**name_or_num
        else:
            return 2**self._bitnum[name_or_num]

    def names(self, mask=None):
        """Return list of names of masked bits.
        If mask=None, return names of all known bits.
        """
        names = list()
        if mask is None:
            for bitnum in sorted(self._bitname.keys()):
                names.append(self._bitname[bitnum])
        else:
            bitnum = 0
            while bitnum**2 <= mask:
                if (2**bitnum & mask):
                    if bitnum in self._bitname.keys():
                        names.append(self._bitname[bitnum])
                    else:
                        names.append('UNKNOWN'+str(bitnum))
                bitnum += 1

        return names

    #- Allow access via mask.BITNAME
    def __getattr__(self, name):
        if name in self._bitnum:
            return 2**self._bitnum[name]
        else:
            raise AttributeError('Unknown mask bit name '+name)

    #- What to print
    def __repr__(self):
        result = list()
        result.append( self._name+':' )
        for i in sorted(self._bitname.keys()):
            result.append('    - [{:16s} {:2d}, "{}"]'.format(self._bitname[i]+',', i, self._comment[i]))

        return "\n".join(result)
