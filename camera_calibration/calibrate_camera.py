import numpy as np
import cv2
import glob

# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
dim_0 = 6
dim_1 = 7

for i in [0,1]:
    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((dim_0*dim_1,3), np.float32)
    objp[:,:2] = np.mgrid[0:dim_1,0:dim_0].T.reshape(-1,2)

    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.

    images = glob.glob('calibration_imgs/cam%d_*.png'%i)

    for fname in images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, (dim_1,dim_0),None)

        # If found, add object points, image points (after refining them)
        if ret == True:
            objpoints.append(objp)

            corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
            imgpoints.append(corners2)

            # Draw and display the corners
            img = cv2.drawChessboardCorners(img, (dim_1, dim_0), corners2,ret)
            cv2.imshow(fname, img)
            cv2.waitKey(500)

    cv2.destroyAllWindows()


    ################# Getting projection matrix ######################
    ret, camera_mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1],None,None)

    # print('camera_mtx', camera_mtx)
    # print("*************")
    # print('rvecs', rvecs)
    # print("*************")
    # print('tvecs', tvecs)
    # print("*************")
    # print('dist', dist)
    # print("*************")
    M = np.matmul(camera_mtx, rvecs[0])
    M = np.concatenate((camera_mtx, tvecs[0]), axis=1)
    M.dump("projection_mtx_%d.npy"%i)
    # print('M', M)
    #
    # print('objpoints', objpoints)
    # print('imgpoints', imgpoints)

################### DISTORT/UNDISTORT STUFF #####################
#
# img = cv2.imread('left12.jpg')
# h,  w = img.shape[:2]
# newcameramtx, roi=cv2.getOptimalNewCameraMatrix(mtx,dist,(w,h),1,(w,h))
#
# # undistort
# dst = cv2.undistort(img, mtx, dist, None, newcameramtx)
#
# # crop the image
# x,y,w,h = roi
# dst = dst[y:y+h, x:x+w]
# cv2.imwrite('calibresult.png',dst)
#
# # undistort
# mapx,mapy = cv2.initUndistortRectifyMap(mtx,dist,None,newcameramtx,(w,h),5)
# dst = cv2.remap(img,mapx,mapy,cv2.INTER_LINEAR)
#
# # crop the image
# x,y,w,h = roi
# dst = dst[y:y+h, x:x+w]
# cv2.imwrite('calibresult.png',dst)
#
# mean_error = 0
# for i in xrange(len(objpoints)):
#     imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
#     error = cv2.norm(imgpoints[i],imgpoints2, cv2.NORM_L2)/len(imgpoints2)
#     tot_error += error
#
# print "total error: ", mean_error/len(objpoints)
#
# # https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_calib3d/py_calibration/py_calibration.html
