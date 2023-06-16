from typing import Union, Set, Tuple, List
from shapely.geometry import Polygon, MultiPolygon
from h3 import h3
from functools import reduce

MultiPolyOrPoly = Union[Polygon, MultiPolygon]


def _extract_coords(polygon: Polygon) -> Tuple[List, List[List]]:
    """Extract the coordinates of outer and inner rings from a Polygon"""
    outer = list(polygon.exterior.coords)
    inners = [list(g.coords) for g in polygon.interiors]
    return outer, inners


def polyfill(
    geometry: MultiPolyOrPoly, resolution: int, geo_json: bool = False, overfill: bool = False
) -> Set[str]:
    """h3.polyfill accepting a shapely (Multi)Polygon

    Parameters
    ----------
    geometry : Polygon or Multipolygon
        Polygon to fill
    resolution : int
        H3 resolution of the filling cells
    geo_json : bool
        If True, coordinates are assumed to be lng/lat. Default: False (lat/lng)
    overfill : bool
        If True, includes h3 cells from outer ring. Default: False

    Returns
    -------
    Set of H3 addresses

    Raises
    ------
    TypeError if geometry is not a Polygon or MultiPolygon
    """
    _max_h3_resolution = 15  # this is the max resolution of the hexes in H3
    if isinstance(geometry, Polygon):
        outer, inners = _extract_coords(geometry)    
        fillers = h3.polyfill_polygon(outer, resolution, inners, geo_json)
        if len(fillers) < 1:
            for i in range(resolution+1, _max_h3_resolution+1):
                fillers = h3.polyfill_polygon(outer, i, inners, geo_json)
                if len(fillers) > 0:
                    # print(f"A hex of resolution: {i} fits the input polygon")
                    temp_fillers = set(fillers)
                    break
            # print(f"Finding it's parent in resolution: {hex_resolution}")
            temp_fillers = set([h3.geo_to_h3(*h3.h3_to_geo(f), resolution) for f in fillers])
        
        else:
            temp_fillers = set(fillers)
        
        if overfill == True:
            temp_fillers = reduce(set.union,[set(h3.k_ring(x,1)) for x in temp_fillers])
        
        return set(temp_fillers)

    elif isinstance(geometry, MultiPolygon):
        h3_addresses = []
        for poly in geometry.geoms:
            h3_addresses.extend(polyfill(poly, resolution, geo_json, overfill))

        return set(h3_addresses)
    else:
        raise TypeError(f"Unknown type {type(geometry)}")