if 'geometry' in kwargs and isinstance(kwargs['geometry'], dict):
            if 'rings' in kwargs['geometry']:
                kwargs['geometry'] = json.dumps(kwargs['geometry'])  # Convert to JSON string if it's a dictionary
        params.update(kwargs)
        print(params)