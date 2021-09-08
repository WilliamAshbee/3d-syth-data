# Spherical tesselations for EEG models (blender python script)
# Copyright (C) 2007, Sergey Plis
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# This code  is heavily  based on the  code of "Geodesic  Dome Design"
# v. 4.8.0 by Richard J. Bono. The math was adopted from there.

import Blender
from Blender import NMesh

from scipy import *
from math import *


# tol - tolerance is a very important parameter here
def clean_float(fnumber):
    tol = 0.0000001
    if fnumber < tol and fnumber > -1.0 * tol:
        fnumber = 0.0
    return fnumber


def topology(frequency):
    vertex = 3
    for i in range(2, frequency + 1):
        vertex += i + 1
    faces = frequency * frequency
    edges = (vertex + faces) - 1
    return [vertex, faces, edges]


def vlabels(vertex, faces, edges, frequency):
    labels = zeros([2, vertex + 1])
    points = zeros([3, vertex + 1])
    count = 1
    for i in range(0, frequency + 1):
        for j in range(0, i + 1):
            labels[0, count] = i
            labels[1, count] = j
            points[0, count] = j
            points[1, count] = i - j
            points[2, count] = frequency - i
            count += 1
    return [points, labels]


def vcoords(points, labels, frequency):
    DEG_TO_RAD = .0174532925199433
    RAD_TO_DEG = 57.2957795130824
    results = points.copy()
    results = results * 0.0
    for i in range(1, size(points, 1)):
        X = points[0, i] * sin(72.0 * DEG_TO_RAD)
        Y = points[1, i] + (points[0, i] * cos(72.0 * DEG_TO_RAD))
        Z = frequency / 2.0 + (points[2, i] / (2.0 * cos(36.0 * DEG_TO_RAD)))
        if (X == Y):
            results[0, i] = 0.0
        elif Y == 0:
            results[0, i] = 90.0
        else:
            results[0, i] = atan(X / Y) * RAD_TO_DEG
        # adjust value to correct quadrant
        if results[0, i] < 0.0:
            results[0, i] += 180
        # now calculate theta
        if (Z == 0):
            results[1, i] = 90.0
        else:
            results[1, i] = atan((pow(pow(X, 2.0) + pow(Y, 2.0), 0.5)) / Z) * RAD_TO_DEG
        # make sure the right quadrant is used
        if (results[1, i] < 0.0):
            results[1, i] += 180.0
        results[2, i] = 1
    return results


def oneface(labels, faceidx, vertex, count, i):
    faceidx[0, count] = i
    for j in range(i, vertex + 1):
        if ((labels[0, j] == labels[0, i] + 1) and (labels[1, j] == labels[1, i])):
            break
    faceidx[1, count] = j
    for k in range(i, vertex + 1):
        if ((labels[0, k] == labels[0, j]) and (labels[1, k] == labels[1, j] + 1)):
            break
    faceidx[2, count] = k
    return 0


def twoface(labels, faceidx, vertex, count, i):
    faceidx[0, count] = i
    for j in range(i, vertex + 1):
        if ((labels[0, j] == labels[0, i] + 1) and (labels[1, j] == labels[1, i] + 1)):
            break
    faceidx[1, count] = j
    for k in range(i, vertex + 1):
        if ((labels[0, k] == labels[0, j] - 1) and (labels[1, k] == labels[1, j])):
            break
    faceidx[2, count] = k
    return 0


def face_factor(vertex, faces, frequency, labels):
    faceidx = zeros([3, faces + 1])
    count = 1
    for i in range(1, vertex - (frequency + 1) + 1):
        if (labels[0, i] == 0 and labels[1, i] == 0):
            oneface(labels, faceidx, vertex, count, i)
            count += 1
        elif (labels[1, i] == 0):
            oneface(labels, faceidx, vertex, count, i)
            count += 1
            twoface(labels, faceidx, vertex, count, i)
            count += 1
        elif (labels[1, i] == labels[0, i]):
            oneface(labels, faceidx, vertex, count, i)
            count += 1
        else:
            oneface(labels, faceidx, vertex, count, i)
            count += 1
            twoface(labels, faceidx, vertex, count, i)
            count += 1
    return faceidx


def sphere2cart(vertices):
    DEG_TO_RAD = .0174532925199433
    for i in range(1, size(vertices, 1)):
        sX = clean_float(cos(vertices[0, i] * DEG_TO_RAD) \
                         * sin(vertices[1, i] * DEG_TO_RAD))
        sY = clean_float(sin(vertices[0, i] * DEG_TO_RAD) \
                         * sin(vertices[1, i] * DEG_TO_RAD))
        sZ = clean_float(cos(vertices[1, i] * DEG_TO_RAD))
        vertices[0, i] = sX
        vertices[1, i] = sY
        vertices[2, i] = sZ
    return 0


def points_facets(frequency):
    [v, f, e] = topology(frequency)
    [vp, lp] = vlabels(v, f, e, frequency)
    vc = vcoords(vp, lp, frequency)
    fidx = face_factor(v, f, frequency, lp)
    sphere2cart(vc)
    return [vc, fidx]


# returns spherical point coordinates
def spoints_facets(frequency):
    [v, f, e] = topology(frequency)
    [vp, lp] = vlabels(v, f, e, frequency)
    vc = vcoords(vp, lp, frequency)
    fidx = face_factor(v, f, frequency, lp)
    return [vc, fidx]


def rotate_phi(phi, phi1, theta1, theta2):
    DEG_TO_RAD = .0174532925199433
    RAD_TO_DEG = 57.2957795130824
    result = (sin(theta1 * DEG_TO_RAD) * sin((phi - phi1) * DEG_TO_RAD)) \
             / sin(theta2 * DEG_TO_RAD)
    if (result > 1.0):
        result = 1.0
    elif (result < -1.0):
        result = -1.0
    return asin(result) * RAD_TO_DEG


def rotate_theta(phi, phi1, theta, theta1):
    DEG_TO_RAD = .0174532925199433
    RAD_TO_DEG = 57.2957795130824
    result = cos(theta1 * DEG_TO_RAD) * cos(theta * DEG_TO_RAD) + \
             sin(theta1 * DEG_TO_RAD) * sin(theta * DEG_TO_RAD) * \
             cos((phi - phi1) * DEG_TO_RAD)
    if (result > 1.0):
        result = 1.0
    elif (result < -1.0):
        result = -1.0
    return acos(result) * RAD_TO_DEG


def icosa_sphere(facenum, points):
    RAD_TO_DEG = 57.2957795130824
    sphere_pnt = points.copy() * 0.0
    if (facenum >= 0 and facenum <= 4):
        for i in range(1, size(points, 1)):
            sphere_pnt[0, i] = points[0, i] + 72.0 * facenum
            sphere_pnt[1, i] = points[1, i]
            sphere_pnt[2, i] = 1.0
    elif (facenum >= 5 and facenum <= 9):
        k = facenum - 5  # phi rotation factor
        for i in range(1, size(points, 1)):
            sphere_pnt[1, i] = rotate_theta(36.0, points[0, i], \
                                            (180.0 - (atan(2.0) * RAD_TO_DEG)), \
                                            points[1, i])
            sphere_pnt[0, i] = (rotate_phi(36.0, points[0, i], points[1, i], \
                                           sphere_pnt[1, i]) + 36.0) + 72.0 * k
            sphere_pnt[2, i] = 1.0
    elif (facenum >= 10 and facenum <= 14):
        k = facenum - 10  # phi rotation factor
        for i in range(1, size(points, 1)):
            sphere_pnt[1, i] = 180.0 - rotate_theta(36.0, points[0, i], \
                                                    (180.0 - (atan(2.0) * RAD_TO_DEG)), \
                                                    points[1, i])
            sphere_pnt[0, i] = (rotate_phi(36.0, points[0, i], points[1, i], \
                                           sphere_pnt[1, i]) + 36.0) + 72.0 * k + 36.0
            sphere_pnt[2, i] = 1.0
    else:
        k = facenum - 15  # phi rotation factor
        for i in range(1, size(points, 1)):
            sphere_pnt[0, i] = (points[0, i] + 72.0 * k) + 36.0
            sphere_pnt[1, i] = 180.0 - points[1, i]
            sphere_pnt[2, i] = 1.0
    return sphere_pnt


def mkIcoTri(R, maxlevel, fnum):
    [points, facets] = spoints_facets(maxlevel)
    sph = icosa_sphere(fnum, points)
    sphere2cart(sph)
    points = sph
    points = points * R
    facets = facets - 1
    me = NMesh.GetRaw()
    for i in range(1, size(points, 1)):
        [x, y, z] = points[:, i]
        v = NMesh.Vert(x, y, z)
        me.verts.append(v)
    for i in range(1, size(facets, 1)):
        [x, y, z] = facets[:, i]
        f = NMesh.Face()
        f.v.append(me.verts[x])
        f.v.append(me.verts[y])
        f.v.append(me.verts[z])
        me.faces.append(f)
    return me


# A function to remove doubles
# The core is almost literal from that of
# slp_import.py by Anthony D'Agostino (Scorpius)
def removeDoubles(mesh):
    # collect verts coordinates for each face into a double array
    faces = []
    for face in mesh.faces:
        faces.append([(face.v[0].co[0], face.v[0].co[1], face.v[0].co[2]), \
                      (face.v[1].co[0], face.v[1].co[1], face.v[1].co[2]), \
                      (face.v[2].co[0], face.v[2].co[1], face.v[2].co[2])])
    # Determine which verts are duplicated, and collect only the non-duplicated
    verts_index = []
    coords = {}  # this is a dictionary
    index = 0
    for i in range(len(faces)):
        for j in range(len(faces[i])):
            vertex = faces[i][j]  # this is a list of the 3 coords
            if not coords.has_key(vertex):
                coords[vertex] = index  # this adds entry vertex:
                # index to the dictionary, where 'vertex' is used as key
                index += 1
                verts_index.append(vertex)
            faces[i][j] = coords[vertex]
    # reset mesh.verts
    mesh.verts = []
    # generate new verts
    for i in range(len(verts_index)):
        x, y, z = verts_index[i]
        mesh.verts.append(Blender.NMesh.Vert(x, y, z))
        # reset mesh.faces
    mesh.faces = []
    # generate new faces
    for i in range(len(faces)):
        numfaceverts = len(faces[i])
        if numfaceverts <= 4:
            new_face = Blender.NMesh.Face()
            for j in range(numfaceverts):
                index = faces[i][j]
                new_face.v.append(mesh.verts[index])

            mesh.faces.append(new_face)


# input is 3xM array - the first and the last row get flipped
def flip_xz(arr):
    tmp = arr[0, :]
    arr[0, :] = arr[2, :]
    arr[2, :] = tmp
    return 0


def mkIcoSphere(R, maxlevel):
    me = NMesh.GetRaw()
    [spoints, sfacets] = spoints_facets(maxlevel)
    sfacets = sfacets - 1
    for fnum in range(0, 20):
        points = icosa_sphere(fnum, spoints)
        sphere2cart(points)
        points = points * R
        for i in range(1, size(points, 1)):
            [x, y, z] = points[:, i]
            v = NMesh.Vert(x, y, z)
            me.verts.append(v)
        if fnum != 0:
            facets = sfacets.copy() + fnum * len(me.verts) / (fnum + 1)
        else:
            facets = sfacets.copy()
        for i in range(1, size(facets, 1)):
            if fnum >= 10:
                [z, y, x] = facets[:, i]
            else:
                [x, y, z] = facets[:, i]
            f = NMesh.Face()
            f.v.append(me.verts[int(x)])
            f.v.append(me.verts[int(y)])
            f.v.append(me.verts[int(z)])
            me.faces.append(f)
    removeDoubles(me)
    return me


def cart2pol(x, y):
    th = atan2(y, x)
    r = sqrt(x ** 2 + y ** 2)
    return th, r


def blin(h, R, theta, maxlevel):
    me = mkIcoSphere(1, maxlevel)
    for i in range(0, size(me.verts, 0)):
        X = me.verts[i].co[0]
        Y = me.verts[i].co[1]
        Z = me.verts[i].co[2]
        [phi, r] = cart2pol(X, Y)
        Z = Z * h / 2
        th = theta * r / (1 + Z / R)
        me.verts[i].co[0] = (Z + R) * sin(th) * cos(phi)
        me.verts[i].co[1] = (Z + R) * sin(th) * sin(phi)
        me.verts[i].co[2] = (Z + R) * cos(th)
    return me


r_brain = 0.8677  # - bran/skull border
r_skull = 0.9467  # - skull/scalp border
r_scalp = 1.0  # - scalp/air border

# the three shells of 3-shell model
# last parameter controls the number of subdivisions - quantity of triangles
mbrain = mkIcoSphere(r_brain, 8)
mskull = mkIcoSphere(r_skull, 8)
mscalp = mkIcoSphere(r_scalp, 8)
# additional pancake-like inclusion inside the skull
# the angle controls how wide the inclusion is
mmesh = blin((r_skull - r_brain) / 2, r_brain + (r_skull - r_brain) / 2, pi / 20, 8)

# comment out corresponding line if you do not want some of the shells to be drawn
NMesh.PutRaw(mbrain, "brain", 1)
NMesh.PutRaw(mskull, "skull", 1)
NMesh.PutRaw(mscalp, "scalp", 1)
NMesh.PutRaw(mmesh, "blin", 1)

Blender.Redraw()