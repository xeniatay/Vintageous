import sublime

import unittest
from collections import namedtuple

from Vintageous.vi.constants import _MODE_INTERNAL_NORMAL
from Vintageous.vi.constants import MODE_NORMAL
from Vintageous.vi.constants import MODE_VISUAL
from Vintageous.vi.constants import MODE_VISUAL_LINE
from Vintageous.vi.constants import MODE_VISUAL_BLOCK

from Vintageous.tests import set_text
from Vintageous.tests import add_sel
from Vintageous.tests import get_sel
from Vintageous.tests import first_sel
from Vintageous.tests import second_sel
from Vintageous.tests import BufferTest


test_data = namedtuple('test_data', 'initial_text regions cmd_params expected actual_func msg')

TESTS = (
    test_data('abc',      [[(0, 2), (0, 2)]], {'mode': MODE_NORMAL}, [(0, 0), (0, 0)], first_sel, ''),
    test_data('abc',      [[(0, 2), (0, 2)]], {'mode': _MODE_INTERNAL_NORMAL}, [(0, 2), (0, 0)], first_sel, ''),
    test_data('abc\nabc', [[(0, 2), (1, 3)]], {'mode': MODE_VISUAL},           [(0, 2), (1, 1)], first_sel, ''),
    test_data('abc\nabc', [[(1, 3), (0, 2)]], {'mode': MODE_VISUAL},           [(1, 3), (0, 0)], first_sel, ''),

    # TODO: Test multiple sels.
)


class Test__vi_zero(BufferTest):
    def testAll(self):
        for (i, data) in enumerate(TESTS):
            # TODO: Perhaps we should ensure that other state is reset too?
            self.view.sel().clear()

            set_text(self.view, data.initial_text)
            for region in data.regions:
                add_sel(self.view, self.R(*region))

            self.view.run_command('_vi_zero', data.cmd_params)

            msg = "[{0}] {1}".format(i, data.msg)
            actual = data.actual_func(self.view)
            self.assertEqual(self.R(*data.expected), actual, msg)
