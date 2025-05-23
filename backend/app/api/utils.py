from flask import request

def parse_bounds(request):
    """Parse geographic bounds from request parameters"""
    north = request.args.get('north', type=float)
    south = request.args.get('south', type=float)
    east = request.args.get('east', type=float)
    west = request.args.get('west', type=float)
    
    if all([north, south, east, west]):
        return {
            'north': north,
            'south': south,
            'east': east,
            'west': west
        }
    return None
