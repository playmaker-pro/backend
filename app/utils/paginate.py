def page_object_elements_count(page_obj):
    """utils which calculate current number of page elemnets
    Used in paginated views

    page_obj.elements = page_obj.end_index() - page_obj.start_index() + 1"""
    return page_obj.end_index() - page_obj.start_index() + 1
