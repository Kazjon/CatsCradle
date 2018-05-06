def centerROI(roi):
    """Returns the center of the roi"""
    return (round(roi[0] + roi[2] / 2), round(roi[1] + roi[3] / 2))


def overlapRatioROIs(roi1, roi2):
    """Returns the overlap ratio of the 2 ROIs
        https://stackoverflow.com/questions/9324339/how-much-do-two-rectangles-overlap
    """
    # Surface intersection
    SI = (max(0, min(roi1[0] + roi1[2], roi2[0] + roi2[2]) - max(roi1[0], roi2[0])) *
          max(0, min(roi1[1] + roi1[3], roi2[1] + roi2[3]) - max(roi1[1], roi2[1])))
    # Surface total
    ST = roi1[2] * roi1[3] + roi2[2] * roi2[3]
    # Surface union
    SU = float(ST - SI)
    overlap = SI / SU
    return overlap

def overlapROIs(roi1, roi2, ratio = 0.75):
    """Returns true if the rois overlap at more than ratio"""
    return (overlapRatioROIs(roi1, roi2) > ratio)



if __name__ == '__main__':
    # Tests
    roi = (5, 0, 4, 7)
    print "Center of (", roi, ") = ", centerROI(roi)

    roi2 = (20, 20, 3, 3)
    roi3 = (4, 3, 10, 3)
    print "(", roi, ") and (", roi, ") overlap at ", 100 * overlapRatioROIs(roi, roi), "% overlap result:", overlapROIs(roi, roi)
    print "(", roi, ") and (", roi2, ") overlap at ", 100 * overlapRatioROIs(roi, roi2), "% overlap result:", overlapROIs(roi, roi2)
    print "(", roi, ") and (", roi3, ") overlap at ", 100 * overlapRatioROIs(roi, roi3), "% overlap result:", overlapROIs(roi, roi3)

    
