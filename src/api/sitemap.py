def generate_sitemap(app):
    output = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            output.append(str(rule))
    return "\n".join(output)