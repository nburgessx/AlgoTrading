# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 11:01:38 2014

@author: peter
"""


# noinspection PyClassHasNoInit
class Printable(object):
    """
    print out all attributes of the class
    Foo=foo
    Bar=bar
    Xyz=xyz
    """
    def __str__(self):
        ans = '''{'''
        for ct in self.__dict__:
            if isinstance(self.__dict__[ct], (dict, int, str, list, tuple, float, type(None))):
                ans += '%s=%s;\n' % (ct, self.__dict__[ct])
            else:
                if hasattr(self.__dict__[ct], '__class__'):
                    ans += '%s=@%s@%s;\n' % (ct, self.__dict__[ct].__class__.__name__, self.__dict__[ct])
                else:
                    ans += '%s=@%s@%s;\n' % (ct, 'NO_CLASS_NAME', self.__dict__[ct])
        return ans[:-2] + '}'  # [:-2] remove the last '\n'


# noinspection PyClassHasNoInit
class PrintableII(object):
    """
    print out all attributes of the class but put them in one line
    {Foo=foo;Bar=bar;Xyz=xyz}
    """
    def __str__(self):
        ans = '''{'''
        for ct in self.__dict__:
            if isinstance(self.__dict__[ct], (dict, int, str, list, tuple, float, type(None))):
                ans += '%s=%s;' % (ct, self.__dict__[ct])
            else:
                ans += '%s=@%s@%s;' % (ct, self.__dict__[ct].__class__.__name__, self.__dict__[ct])
        return ans[:-1] + '}'
