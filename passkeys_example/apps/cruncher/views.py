import glob
import os

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import Http404, render
from django.template import engines
from django.template.exceptions import TemplateDoesNotExist


# Some shenigans required
base_template_name_extends = '{' + '% exten' + 'ds "base' + '.html" %' + '}'

INDEX = f"""
"{base_template_name_extends}"
style="padding:2rem" class=""

<h1>Index of </h1>
<hr />
<ul style="margin:2rem">

</ul>

"""


def template_folder(request, path, document_root="", show_indexes=False):
    if not settings.DEBUG and not request.user.is_staff:
        raise Http404

    actual_path = os.path.join(document_root, path)
    try:
        return render(request, actual_path)
    except TemplateDoesNotExist:
        raise Http404
    except IsADirectoryError:
        if show_indexes:
            template_dir = os.path.abspath(settings.TEMPLATES[0].get("DIRS")[0])
            dir = os.path.abspath(os.path.join(template_dir, document_root))

            templates = glob.glob(dir + "/*.html")
            templates = [t.replace(template_dir, "") for t in templates]
            index_template = engines["django"].from_string(INDEX)
            return HttpResponse(
                index_template.render(
                    context={"index_templates": templates, "path": document_root},
                    request=request,
                )
            )

        raise Http404
