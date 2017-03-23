from bakery.views import BuildableTemplateView


def template_view_creator(name, template_name, build_path):
    return type(
        name, (BuildableTemplateView, ),
        {'template_name': template_name, 'build_path': build_path}
    )
