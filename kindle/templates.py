# coding:utf-8

"""
Simple file to provide CONSTANT of templates contents to Periodical
"""

import os
PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))

# {$title} {$creator} {$description} {$title} {$content}
FILE_ARTICLE = open(PROJECT_DIR+"/templates/article.template", 'r')
ARTICLE_STR = FILE_ARTICLE.read()

# {$id} {$play_order} {$title} {$id} {$description} {$author}
FILE_ARTICLE_NCX = open(PROJECT_DIR+"/templates/article_ncx.template", 'r')
ARTICLE_NCX_STR = FILE_ARTICLE_NCX.read()

# {$identifier} {$title} {$creator} {$publisher} {$subject} {$description} {$date} {$items_manifest} {$items_ref}
FILE_CONTENTS_OPF = open(PROJECT_DIR+"/templates/content_opf.template", 'r')
CONTENTS_OPF_STR = FILE_CONTENTS_OPF.read()

# {$sections}
FILE_CONTENTS = open(PROJECT_DIR+"/templates/contents.template", 'r')
CONTENTS_STR = FILE_CONTENTS.read()

# {$title} {$creator} {$sections}
FILE_NAV_CONTENTS_NCX = open(PROJECT_DIR+"/templates/nav-contents_ncx.template", 'r')
NAV_CONTENTS_NCX_STR = FILE_NAV_CONTENTS_NCX.read()

# {$section_id} {$play_order} {$section_title} {$section_first} {$articles}
FILE_SECTION_NCX = open(PROJECT_DIR+"/templates/section_ncx.template", 'r')
SECTION_NCX_STR = FILE_SECTION_NCX.read()
