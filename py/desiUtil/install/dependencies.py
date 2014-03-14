# License information goes here
# -*- coding: utf-8 -*-
def dependencies(product,mydeps=None,modulefile=False):
    """Process the dependencies for a software product.

    Parameters
    ----------
    product : str
        Name of the product to get dependencies for.
    mydeps : list, optional
        A list of additional dependency files to read.
    modulefile : bool, optional
        If set to ``True``, dependencies will be processed in preparation
        for inserting them into a module file.

    Returns
    -------
    dependencies : list
        Returns the list of dependencies.  If the dependency file is not
        found, or if the product is not listed, the list will be empty.
    """
    from ConfigParser import SafeConfigParser
    from os import getenv
    from os.path import join
    depfiles = [join(getenv('DESIUTIL_DIR'),'etc','dependencies.cfg')]
    if mydeps is not None:
        depfiles = mydeps + depfiles
    config = SafeConfigParser()
    config.optionxform = str
    read = config.read(depfiles)
    deps = list()
    if len(read) == 0:
        return deps
    if not config.has_section(product):
        return deps
    for n,v in config.items(product):
        vv = v.split(',')
        req = vv[0].strip()
        vers = vv[1].strip()
        if vers == 'default':
            pv = n
        else:
            pv = "{0}/{1}".format(n,vers)
        if modulefile:
            deps.append('module load {0}'.format(pv))
            if req == 'required':
                deps.append('prereq {0}'.format(pv))
        else:
            deps.append(pv)
    return deps
